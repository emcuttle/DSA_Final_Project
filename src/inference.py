import os
import logging
import uuid

import geopandas as gpd
from shapely import wkt
import rasterio

from ultralytics import YOLO

from utils import (
    RAW_DIR,
    DATASETS_DIR,
    RESULTS_DIR,
    MODELS_DIR,
    download_geotiff,
    download_file,
    unzip_file,
    query_gdb_contained_by_polygon,
    build_valid_data_boundary,
    prepare_sar_dataset,
)

logger = logging.getLogger("inference")


MARSHALL_SAR_URL = (
    "https://capella-open-data.s3.amazonaws.com/data/2021/12/31/"
    "CAPELLA_C03_SP_GEO_HH_20211231164052_20211231164115/"
    "CAPELLA_C03_SP_GEO_HH_20211231164052_20211231164115.tif"
)

MARSHALL_FOOTPRINTS_URL = (
    "https://fema-femadata.s3.amazonaws.com/Partners/ORNL/USA_Structures/"
    "Colorado/Deliverable20230630CO.zip"
)

CO_WKT = (
    "POLYGON ((-105.190315 39.922639, -105.072212 39.922639,"
    " -105.072212 39.998953, -105.190315 39.998953, -105.190315 39.922639))"
)


def prepare_marshall_test_dataset():
    # download SAR data
    sar_path = download_geotiff(MARSHALL_SAR_URL, output_dir=RAW_DIR)

    # dowload building footprints
    zip_path = os.path.join(RAW_DIR, "co_structures.zip")
    download_file(MARSHALL_FOOTPRINTS_URL, zip_path)
    extract_dir = os.path.join(RAW_DIR, "co_structures")
    unzip_file(zip_path, extract_dir)

    # Find GDB path
    gdb_path = None
    for root, dirs, files in os.walk(extract_dir):
        for d in dirs:
            if d.endswith(".gdb"):
                gdb_path = os.path.join(root, d)
                break
        if gdb_path:
            break
    if gdb_path is None:
        raise FileNotFoundError("Could not find GDB path in building footprints data.")

    layer_name = "CO_Structures"

    # AOI polygon
    p = wkt.loads(CO_WKT)
    polygon_gdf = gpd.GeoDataFrame([1], geometry=[p], crs="EPSG:4326")

    contained_features = query_gdb_contained_by_polygon(
        gdb_path, layer_name, polygon_gdf
    )
    contained_features = contained_features.explode(index_parts=False)

    gdf_co = contained_features.copy()
    gdf_co = gdf_co.to_crs("EPSG:32610")
    gdf_co["geometry"] = gdf_co.buffer(5)

    gdf_co["label"] = 0

    ids = [str(uuid.uuid4()) for _ in range(len(gdf_co))]
    gdf_co.index = ids
    gdf_co.index.name = "id"

    # build AOI bounding box for cropping + valid data boundary
    with rasterio.open(sar_path) as src:
        if gdf_co.crs != src.crs:
            gdf_co = gdf_co.to_crs(src.crs)

        all_polygons_merged = gdf_co.unary_union
        bounding_box = all_polygons_merged.envelope
        gdf_aoi = gpd.GeoDataFrame.from_features(
            [{"geometry": bounding_box, "properties": {"name": "marshall_aoi"}}],
            crs=gdf_co.crs,
        )

        aoi_boundary = gdf_aoi.unary_union
        valid_data_boundary = build_valid_data_boundary(src)
        final_boundary = aoi_boundary.intersection(valid_data_boundary)

        if final_boundary.is_empty:
            logger.warning("AOI and valid SAR data do not overlap; no chips generated.")
            return None, None

        gdf_fully_inside = gdf_co[gdf_co.within(final_boundary)].copy()

    dataset_dir = os.path.join(DATASETS_DIR, "marshall_test_dataset")
    prepare_sar_dataset(
        gdf_fully_inside,
        sar_path,
        dataset_dir,
        target_size=(224, 224),
        split_ratios=(0.0, 0.0, 1.0),
        random_state=42,
    )

    return dataset_dir, gdf_fully_inside


def run_inference_on_marshall():
    model_path = os.path.join(MODELS_DIR, "building_damage_classifier_best.pt")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}."
        )

    logger.info("Preparing Marshall test dataset...")
    dataset_dir, gdf_fully_inside = prepare_marshall_test_dataset()
    if dataset_dir is None:
        logger.warning("Marshall dataset preparation failed.")
        return

    test_dir = os.path.join(dataset_dir, "test", "0")
    logger.info(f"Running inference on Marshall test images at: {test_dir}")

    model = YOLO(model_path)
    results = model(test_dir, verbose=False)

    # build predictions dataframe
    import pandas as pd
    import os as _os

    rows = []
    for res in results:
        fname = _os.path.basename(res.path)
        top1_idx = res.probs.top1
        pred_name = res.names[top1_idx]
        rows.append({"image_id": fname, "prediction_class": pred_name})

    df_pred = pd.DataFrame(rows)
    df_pred["id"] = df_pred["image_id"].str.split("_", expand=True)[1].str.split(
        ".", expand=True
    )[0]

    # save predictions as csv
    os.makedirs(RESULTS_DIR, exist_ok=True)
    preds_csv = os.path.join(RESULTS_DIR, "marshall_predictions.csv")
    df_pred.to_csv(preds_csv, index=False)
    logger.info(f"Saved Marshall predictions to: {preds_csv}")


def main():
    logger.info("Running inference on Marshall wildfire building area...")
    run_inference_on_marshall()
    logger.info("Inference complete.")


if __name__ == "__main__":
    main()
