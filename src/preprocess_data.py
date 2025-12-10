import os
import uuid
import logging
import geopandas as gpd
import rasterio
from shapely.geometry import box

from utils import (
    RAW_DIR,
    DATASETS_DIR,
    prepare_sar_dataset,
)

logger = logging.getLogger("preprocess_data")


def build_palisades_dataset():
    palisades_gpkg = os.path.join(RAW_DIR, "maxar_palisades_damage.gpkg")
    palisades_sar = None

    for f in os.listdir(RAW_DIR):
        if "CAPELLA_C14_SS_GEO_HH_20250111163649" in f and f.endswith(".tif"):
            palisades_sar = os.path.join(RAW_DIR, f)
            break
    if palisades_sar is None:
        raise FileNotFoundError("Palisades SAR data not found in RAW_DIR")

    gdf_mx = gpd.read_file(palisades_gpkg)

    # label column
    gdf_mx["label"] = gdf_mx["damaged"]

    # project and buffer
    gdf_mx = gdf_mx.to_crs("EPSG:32611")
    gdf_mx["geometry"] = gdf_mx.buffer(5)

    # UUID index
    uuids = [str(uuid.uuid4()) for _ in range(len(gdf_mx))]
    gdf_mx.index = uuids
    gdf_mx.index.name = "uuid"
    gdf_mx = gdf_mx[["geometry", "label"]]

    with rasterio.open(palisades_sar) as src:
        if gdf_mx.crs != src.crs:
            gdf_mx = gdf_mx.to_crs(src.crs)

        # AOI bounding box
        all_polygons_merged = gdf_mx.unary_union
        bounding_box = all_polygons_merged.envelope
        aoi_gdf = gpd.GeoDataFrame.from_features(
            [{"geometry": bounding_box, "properties": {"name": "palisades_aoi"}}],
            crs=gdf_mx.crs,
        )

        aoi_boundary = aoi_gdf.unary_union
        gdf_fully_inside = gdf_mx[gdf_mx.within(aoi_boundary)].copy()

    dataset_dir = os.path.join(DATASETS_DIR, "palisades_building_dataset")
    prepare_sar_dataset(
        gdf_fully_inside,
        palisades_sar,
        dataset_dir,
        target_size=(224, 224),
        split_ratios=(0.7, 0.15, 0.15),
        random_state=42,
    )
    logger.info(f"Palisades dataset prepared at: {dataset_dir}")


def build_lahaina_dataset():
    lahaina_geojson = os.path.join(RAW_DIR, "lahaina_buildings.geojson")
    lahaina_sar = None
    
    for f in os.listdir(RAW_DIR):
        if "CAPELLA_C06_SP_GEO_HH_20230812045610" in f and f.endswith(".tif"):
            lahaina_sar = os.path.join(RAW_DIR, f)
            break
    if lahaina_sar is None:
        raise FileNotFoundError("Lahaina SAR .tif not found in RAW_DIR")

    gdf_bldg = gpd.read_file(lahaina_geojson)

    gdf_bldg = gdf_bldg.to_crs("EPSG:32604")
    gdf_bldg["geometry"] = gdf_bldg.buffer(5)
    # map ClassLabel to binary
    gdf_bldg["label"] = gdf_bldg["ClassLabel"].map({"Damaged": 1, "Undamaged": 0})

    uuids = [str(uuid.uuid4()) for _ in range(len(gdf_bldg))]
    gdf_bldg.index = uuids
    gdf_bldg.index.name = "uuid"
    gdf_bldg = gdf_bldg[["geometry", "label"]]

    with rasterio.open(lahaina_sar) as src:
        if gdf_bldg.crs != src.crs:
            gdf_bldg = gdf_bldg.to_crs(src.crs)

        all_polygons_merged = gdf_bldg.unary_union
        bounding_box = all_polygons_merged.envelope
        aoi_gdf = gpd.GeoDataFrame.from_features(
            [{"geometry": bounding_box, "properties": {"name": "lahaina_aoi"}}],
            crs=gdf_bldg.crs,
        )

        aoi_boundary = aoi_gdf.unary_union
        gdf_fully_inside = gdf_bldg[gdf_bldg.within(aoi_boundary)].copy()

    dataset_dir = os.path.join(DATASETS_DIR, "lahaina_building_dataset")
    prepare_sar_dataset(
        gdf_fully_inside,
        lahaina_sar,
        dataset_dir,
        target_size=(224, 224),
        split_ratios=(0.7, 0.15, 0.15),
        random_state=42,
    )
    logger.info(f"Lahaina dataset prepared at: {dataset_dir}")


def main():
    logger.info("Building Palisades & Lahaina chip datasets...")
    build_palisades_dataset()
    build_lahaina_dataset()
    logger.info("Preprocessing complete.")


if __name__ == "__main__":
    main()
