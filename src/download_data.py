import os
import logging
import geopandas as gpd
import fiona

from utils import RAW_DIR, download_geotiff, download_file

logger = logging.getLogger("download_data")


# data URLs
PALISADES_FOOTPRINTS_URL = (
    "https://data.humdata.org/dataset/30768ff0-289b-4fda-96d9-7209243c984d/"
    "resource/9650c5fe-c29b-429e-81e3-537688a74f60/"
    "download/maxar_palisades_1050010040277500_damage_predictions.gpkg"
)

PALISADES_SAR_URL = (
    "https://capella-open-data.s3.amazonaws.com/data/2025/1/11/"
    "CAPELLA_C14_SS_GEO_HH_20250111163649_20250111163705/"
    "CAPELLA_C14_SS_GEO_HH_20250111163649_20250111163705.tif"
)

LAHAINA_SAR_URL = (
    "https://capella-open-data.s3.amazonaws.com/data/2023/8/12/"
    "CAPELLA_C06_SP_GEO_HH_20230812045610_20230812045634/"
    "CAPELLA_C06_SP_GEO_HH_20230812045610_20230812045634.tif"
)

# Lahaina ArcGIS FeatureServer
LAHAINA_FOOTPRINTS_URL = (
    "https://services1.arcgis.com/uujCiiEZAflDbdxE/arcgis/rest/services/"
    "InferencedBuildingDamage/FeatureServer/2/query"
)


def download_palisades_data():
    palisades_gpkg = os.path.join(RAW_DIR, "maxar_palisades_damage.gpkg")
    download_file(PALISADES_FOOTPRINTS_URL, palisades_gpkg)

    # testing
    try:
        layer_names = fiona.listlayers(PALISADES_FOOTPRINTS_URL)
        layer_name = layer_names[0]
    except Exception:
        layer_name = None

    if layer_name:
        gdf_mx = gpd.read_file(PALISADES_FOOTPRINTS_URL, layer=layer_name)
        gdf_mx.to_file(palisades_gpkg, driver="GPKG")
        logger.info(f"Saved Palisades GPKG to {palisades_gpkg}")

    palisades_sar = download_geotiff(PALISADES_SAR_URL, output_dir=RAW_DIR)
    logger.info(f"Palisades SAR saved at: {palisades_sar}")


def download_lahaina_data():
    # Download Lahaina building footprints
    import geopandas as gpd
    import requests

    logger.info("Downloading Lahaina building footprints...")
    gdf_list = []
    offset = 0
    page_size = 2000

    # First get total count
    count_params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    r = requests.get(LAHAINA_FOOTPRINTS_URL, params=count_params)
    r.raise_for_status()
    total_features = r.json()["count"]
    logger.info(f"Total Lahaina features to download: {total_features}")

    while offset < total_features:
        logger.info(f"Fetching Lahaina features {offset}–{offset + page_size}")
        query_params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }

        page_url = (
            f"{LAHAINA_FOOTPRINTS_URL}?"
            + "&".join([f"{k}={v}" for k, v in query_params.items()])
        )
        page_gdf = gpd.read_file(page_url)
        if page_gdf.empty:
            break
        gdf_list.append(page_gdf)
        offset += len(page_gdf)

    if not gdf_list:
        raise RuntimeError("No Lahaina features downloaded.")

    gdf_bldg = gpd.pd.concat(gdf_list, ignore_index=True)
    lahaina_geojson = os.path.join(RAW_DIR, "lahaina_buildings.geojson")
    gdf_bldg.to_file(lahaina_geojson, driver="GeoJSON")
    logger.info(f"Lahaina buildings saved to {lahaina_geojson}")

    lahaina_sar = download_geotiff(LAHAINA_SAR_URL, output_dir=RAW_DIR)
    logger.info(f"Lahaina SAR saved at: {lahaina_sar}")


def main():
    logger.info("Downloading raw data for Palisades and Lahaina...")
    download_palisades_data()
    download_lahaina_data()
    logger.info("All data downloads complete.")


if __name__ == "__main__":
    main()
