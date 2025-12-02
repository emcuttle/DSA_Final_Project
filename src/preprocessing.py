import os
import shutil
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
from PIL import Image
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import geopandas as gpd


# --- Helper Functions ---

def _safe_stratified_split(gdf, test_size, random_state):
    """
    Stratified train/test split, falls back to non-stratified if class imbalance occurs.
    """
    if gdf.empty:
        return gdf.copy(), gdf.copy()  # Return empty splits
    try:
        train_gdf, test_gdf = train_test_split(
            gdf, test_size=test_size, random_state=random_state, stratify=gdf['label']
        )
    except ValueError:
        train_gdf, test_gdf = train_test_split(
            gdf, test_size=test_size, random_state=random_state, stratify=None
        )
    return train_gdf, test_gdf


def _process_and_save(df, split_name, raster_src, output_dir, target_size):
    """
    Processes SAR image chips and saves them into labeled folders for training.
    """
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc=f"Processing {split_name} set"):
        geom = [row.geometry]
        label = row['label']
        image_name = f"building_{index}.png"

        try:
            out_image, _ = mask(raster_src, geom, crop=True, nodata=0)
            out_image = out_image[0]  # Take first band

            # Normalize to 0-255
            valid_pixels = out_image[out_image != 0]
            if valid_pixels.size > 0:
                vmin, vmax = np.percentile(valid_pixels, (2, 98))
                if vmax > vmin:
                    out_image = np.clip(out_image, vmin, vmax)
                    out_image = ((out_image - vmin) / (vmax - vmin) * 255).astype(np.uint8)
                else:
                    out_image = np.full(out_image.shape, 128, dtype=np.uint8)
            else:
                out_image = np.zeros(out_image.shape, dtype=np.uint8)

            # Pad image to target size
            h, w = out_image.shape
            canvas = np.zeros(target_size, dtype=np.uint8)
            y_offset = (target_size[0] - h) // 2
            x_offset = (target_size[1] - w) // 2
            canvas[y_offset:y_offset+h, x_offset:x_offset+w] = out_image

            # Save to directory
            save_path = os.path.join(output_dir, split_name, str(label))
            os.makedirs(save_path, exist_ok=True)
            Image.fromarray(canvas).save(os.path.join(save_path, image_name))

        except Exception as e:
            print(f"Error processing building {index}: {e}")


# --- Main Preprocessing Function ---

def prepare_sar_dataset(gdf, raster_file_path, output_dir, target_size=(256, 256),
                        split_ratios=(0.7, 0.15, 0.15), random_state=42):
    """
    Prepares SAR dataset: filters footprints, splits into train/val/test, saves images.
    """
    print("--- Starting Dataset Preparation ---")

    try:
        with rasterio.open(raster_file_path) as src:

            # Filter footprints fully contained within raster
            raster_bounds_poly = box(*src.bounds)
            if gdf.crs != src.crs:
                gdf = gdf.to_crs(src.crs)

            initial_count = len(gdf)
            gdf = gdf[gdf.geometry.within(raster_bounds_poly)].copy()
            filtered_count = len(gdf)
            print(f"Filtered {initial_count - filtered_count} footprints outside raster bounds.")

            if filtered_count == 0:
                print("No footprints fully within raster bounds. Exiting.")
                return

            # Stratified split
            train_val_gdf, test_gdf = _safe_stratified_split(gdf, test_size=split_ratios[2], random_state=random_state)
            val_ratio_of_trainval = split_ratios[1] / (split_ratios[0] + split_ratios[1])
            train_gdf, val_gdf = _safe_stratified_split(train_val_gdf, test_size=val_ratio_of_trainval, random_state=random_state)

            print(f"Training samples: {len(train_gdf)}, Validation samples: {len(val_gdf)}, Test samples: {len(test_gdf)}")

            # Process and save images
            if not train_gdf.empty:
                _process_and_save(train_gdf, 'train', src, output_dir, target_size)
            if not val_gdf.empty:
                _process_and_save(val_gdf, 'val', src, output_dir, target_size)
            if not test_gdf.empty:
                _process_and_save(test_gdf, 'test', src, output_dir, target_size)

        print("--- Dataset Preparation Complete ---")

    except rasterio.errors.RasterioIOError:
        print(f"Error: Could not open raster file at '{raster_file_path}'")
    except Exception as e:
        print(f"Unexpected error: {e}")
