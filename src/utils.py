import os
import shutil
import uuid
import logging
import zipfile
import urllib.parse

import numpy as np
import pandas as pd
import requests
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.errors import RasterioIOError
from rasterio.features import shapes
from shapely.geometry import box, shape
from shapely.ops import unary_union

# create paths/directories
DATA_ROOT = "/data"
RAW_DIR = os.path.join(DATA_ROOT, "raw")
PROCESSED_DIR = os.path.join(DATA_ROOT, "processed")
DATASETS_DIR = os.path.join(DATA_ROOT, "datasets")
MODELS_DIR = os.path.join(DATA_ROOT, "models")
RESULTS_DIR = os.path.join(DATA_ROOT, "results")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sar_utils")


# create functions
def download_file(url: str, local_path: str, overwrite: bool = False) -> str:
    """
    Downloads a file from URL to local_path if it doesn't exist or overwrite=True.
    """
    if os.path.exists(local_path) and not overwrite:
        logger.info(f"File already exists, skipping download: {local_path}")
        return local_path

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    logger.info(f"Downloading {url} -> {local_path}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    logger.info(f"Saved: {local_path}")
    return local_path


def download_geotiff(url: str, output_dir: str = RAW_DIR, overwrite: bool = False) -> str:
    """
    Downloads a GeoTIFF from URL and saves it in output_dir.
    Returns the full local path.
    """
    path = urllib.parse.urlparse(url).path
    filename = os.path.basename(path)
    if not filename:
        raise ValueError(f"Could not determine filename from URL: {url}")

    local_path = os.path.join(output_dir, filename)
    return download_file(url, local_path, overwrite=overwrite)


def unzip_file(zip_path: str, extract_to_path: str) -> None:
    """
    Unzips a specified zip file to a target directory.
    """
    logger.info(f"Unzipping {zip_path} -> {extract_to_path}")
    os.makedirs(extract_to_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to_path)
    logger.info("Unzip complete.")


def _process_and_save(df, split_name, raster_src, output_dir, target_size):
    """
    Internal helper to extract SAR chips for a split and save PNGs.
    """
    from PIL import Image

    for idx, row in df.iterrows():
        geom = [row.geometry]
        label = row["label"]
        image_name = f"building_{idx}.png"

        try:
            out_image, _ = mask(raster_src, geom, crop=True, nodata=0)
            out_image = out_image[0]  # first band

            if out_image.size == 0:
                continue

            valid_pixels = out_image[out_image != 0]
            if valid_pixels.size > 0:
                vmin, vmax = np.percentile(valid_pixels, (2, 98))
                if vmax > vmin:
                    out_image = np.clip(out_image, vmin, vmax)
                    out_image = ((out_image - vmin) / (vmax - vmin) * 255).astype(
                        np.uint8
                    )
                else:
                    out_image = np.full(out_image.shape, 128, dtype=np.uint8)
            else:
                out_image = np.zeros(out_image.shape, dtype=np.uint8)

            h, w = out_image.shape
            canvas = np.zeros(target_size, dtype=np.uint8)
            y_off = (target_size[0] - h) // 2
            x_off = (target_size[1] - w) // 2
            canvas[y_off : y_off + h, x_off : x_off + w] = out_image

            out_dir = os.path.join(output_dir, split_name, str(label))
            os.makedirs(out_dir, exist_ok=True)
            output_path = os.path.join(out_dir, image_name)
            Image.fromarray(canvas).save(output_path)
        except Exception as e:
            logger.warning(f"Error processing building {idx}: {e}")


def _safe_stratified_split(gdf, test_size, random_state):
    """
    Wrapper for train_test_split that handles stratification errors.
    """
    from sklearn.model_selection import train_test_split

    if gdf.empty:
        return gdf.copy(), gdf.copy()
    if test_size == 0.0:
        return gdf.copy(), gdf.head(0).copy()
    if test_size == 1.0:
        return gdf.head(0).copy(), gdf.copy()

    try:
        train_gdf, test_gdf = train_test_split(
            gdf,
            test_size=test_size,
            random_state=random_state,
            stratify=gdf["label"],
        )
    except ValueError as e:
        if "least populated class" in str(e):
            logger.warning(
                f"Stratification failed ({e}), using non-stratified split instead."
            )
            train_gdf, test_gdf = train_test_split(
                gdf, test_size=test_size, random_state=random_state, stratify=None
            )
        else:
            raise
    return train_gdf, test_gdf


def prepare_sar_dataset(
    gdf,
    raster_file_path,
    output_dir,
    target_size=(256, 256),
    split_ratios=(0.7, 0.15, 0.15),
    random_state=42,
):
    """
    Prepares a SAR image dataset by extracting chips and splitting into
    train/val/test, saving PNGs in YOLO classification folder structure.

    gdf: GeoDataFrame with 'geometry' and 'label'
    """
    logger.info(f"Preparing SAR dataset -> {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        with rasterio.open(raster_file_path) as src:
            raster_bounds_poly = box(*src.bounds)

            if gdf.crs != src.crs:
                logger.info(f"Reprojecting GDF from {gdf.crs} to {src.crs}")
                gdf = gdf.to_crs(src.crs)

            initial_count = len(gdf)
            gdf = gdf[gdf.geometry.within(raster_bounds_poly)].copy()
            filtered_count = len(gdf)
            if filtered_count < initial_count:
                logger.info(
                    f"Filtered out {initial_count - filtered_count} footprints "
                    "outside raster bounds."
                )
            if filtered_count == 0:
                logger.error(
                    "No footprints fully within raster bounds; dataset prep aborted."
                )
                return

            train_prop, val_prop, test_prop = split_ratios
            if not np.isclose(sum(split_ratios), 1.0):
                raise ValueError(
                    f"split_ratios must sum to 1.0, got {sum(split_ratios)}"
                )

            if not all(0.0 <= p <= 1.0 for p in split_ratios):
                raise ValueError("split_ratios must be between 0 and 1")

            train_val_gdf, test_gdf = _safe_stratified_split(
                gdf, test_size=test_prop, random_state=random_state
            )

            train_plus_val_prop = train_prop + val_prop
            if train_plus_val_prop > 0:
                val_ratio_of_rest = val_prop / train_plus_val_prop
            else:
                val_ratio_of_rest = 0.0

            train_gdf, val_gdf = _safe_stratified_split(
                train_val_gdf,
                test_size=val_ratio_of_rest,
                random_state=random_state,
            )

            logger.info(
                f"Split sizes -> train: {len(train_gdf)}, "
                f"val: {len(val_gdf)}, test: {len(test_gdf)}"
            )

            if not train_gdf.empty:
                _process_and_save(train_gdf, "train", src, output_dir, target_size)
            if not val_gdf.empty:
                _process_and_save(val_gdf, "val", src, output_dir, target_size)
            if not test_gdf.empty:
                _process_and_save(test_gdf, "test", src, output_dir, target_size)

    except RasterioIOError:
        logger.error(f"Could not open raster file: {raster_file_path}")
    except Exception as e:
        logger.error(f"Unexpected error in prepare_sar_dataset: {e}")

    logger.info("SAR dataset preparation complete.")


def _copy_contents(source_dir, dest_dir):
    logger.info(f"Merging from: {source_dir}")
    for root, _, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        dest_path_dir = os.path.join(dest_dir, rel_path)
        os.makedirs(dest_path_dir, exist_ok=True)

        for filename in files:
            src_fp = os.path.join(root, filename)
            dst_fp = os.path.join(dest_path_dir, filename)
            if os.path.exists(dst_fp):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dst_fp):
                    new_name = f"{base}_merged_{counter}{ext}"
                    dst_fp = os.path.join(dest_path_dir, new_name)
                    counter += 1
                logger.info(f"Name conflict; renaming to {new_name}")
            shutil.copy2(src_fp, dst_fp)


def merge_and_copy_directories(dir1, dir2, new_dir):
    """
    Merges two YOLO-style directory trees into new_dir.
    """
    if os.path.exists(new_dir):
        raise RuntimeError(f"Destination directory already exists: {new_dir}")

    logger.info(f"Creating merged dataset: {new_dir}")
    os.makedirs(new_dir, exist_ok=True)
    _copy_contents(dir1, new_dir)
    _copy_contents(dir2, new_dir)
    logger.info("Merge complete.")


def query_gdb_contained_by_polygon(gdb_path, layer_name, polygon_gdf):
    """
    Queries a FileGDB layer and returns rows fully contained
    in polygon_gdf (single polygon).
    """
    gdf = gpd.read_file(gdb_path, layer=layer_name)
    if len(polygon_gdf) != 1:
        raise ValueError("polygon_gdf must contain exactly one polygon.")

    poly = polygon_gdf.geometry.iloc[0]

    if gdf.crs != polygon_gdf.crs:
        gdf = gdf.to_crs(polygon_gdf.crs)

    contained = gdf[gdf.geometry.within(poly)]
    return contained


def build_valid_data_boundary(src):
    """
    Builds a polygon representing valid raster data
    from the nodata mask.
    """
    mask_arr = src.read_masks(1)
    valid_geoms = list(
        shapes(mask_arr, mask=(mask_arr == 255), transform=src.transform)
    )
    if not valid_geoms:
        raise ValueError("No valid data found in raster.")

    valid_polys = [shape(geom) for geom, val in valid_geoms]
    return unary_union(valid_polys)
