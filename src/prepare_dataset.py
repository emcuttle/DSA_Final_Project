import os
import yaml
import logging

from utils import DATASETS_DIR, merge_and_copy_directories

logger = logging.getLogger("prepare_dataset")


def main():
    palisades_dir = os.path.join(DATASETS_DIR, "palisades_building_dataset")
    lahaina_dir = os.path.join(DATASETS_DIR, "lahaina_building_dataset")
    merged_dir = os.path.join(DATASETS_DIR, "building_dataset")

    if not os.path.isdir(palisades_dir):
        raise FileNotFoundError(palisades_dir)
    if not os.path.isdir(lahaina_dir):
        raise FileNotFoundError(lahaina_dir)

    logger.info("Merging Palisades & Lahaina datasets...")
    merge_and_copy_directories(palisades_dir, lahaina_dir, merged_dir)

    yaml_path = os.path.join(DATASETS_DIR, "data.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(data_yaml, f)
    logger.info(f"Dataset YAML to path: {yaml_path}")
    logger.info(f"Merged dataset directory: {merged_dir}")


if __name__ == "__main__":
    main()
