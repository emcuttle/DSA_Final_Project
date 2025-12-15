## Dataset General Information

Four datasets were used in this project. Building damage vector data and SAR imagery
from both the Palisades Wildfire (California) and the Lahaina Wildfire (Hawaii) were
loaded via a Kubernetes download job (`job-download.yaml`) and stored on a PVC in 
the Nautilus environment for use in model training and evaluation.

**Special Note:** Although Lahaina Wildfire data was downloaded and preprocessed as part
of the pipeline, only the Palisades Wildfire datasets were used to train the model in order 
to simplify the project scope.

---

## Dataset Locations and Sources

All datasets were accessed via URLs and downloaded into the Nautilus PVC.

### Palisades, California

- **Building Footprints**  
  Sourced from the Humanitarian Data Exchange (HDX), derived from Maxar Technologies
  damage predictions.  
  Format: GeoPackage (vector)  
  https://data.humdata.org/dataset/30768ff0-289b-4fda-96d9-7209243c984d/resource/9650c5fe-c29b-429e-81e3-537688a74f60/download/maxar_palisades_1050010040277500_damage_predictions.gpkg

- **SAR Imagery**  
  Sourced from Capella Space Open Data.  
  Format: GeoTIFF (raster)  
  https://capella-open-data.s3.amazonaws.com/data/2025/1/11/CAPELLA_C14_SS_GEO_HH_20250111163649_20250111163705/CAPELLA_C14_SS_GEO_HH_20250111163649_20250111163705.tif

### Lahaina, Hawaii

- **Building Footprints**  
  Sourced from an ArcGIS Online hosted Feature Service (Esri) and accessed via the
  ArcGIS REST API.  
  Format: Vector feature service  
  https://services1.arcgis.com/uujCiiEZAflDbdxE/arcgis/rest/services/InferencedBuildingDamage/FeatureServer/2/query

- **SAR Imagery**  
  Sourced from Capella Space Open Data.  
  Format: GeoTIFF (raster)  
  https://capella-open-data.s3.amazonaws.com/data/2023/8/12/CAPELLA_C06_SP_GEO_HH_20230812045610_20230812045634/CAPELLA_C06_SP_GEO_HH_20230812045610_20230812045634.tif
