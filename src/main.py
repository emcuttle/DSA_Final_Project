import logging

from download_data import main as download_main
from preprocess_data import main as preprocess_main
from prepare_dataset import main as prepare_dataset_main
from train_model import main as train_main
from evaluate_model import main as eval_main
from inference import main as inference_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main_pipeline")


def main():
    logger.info("Starting SAR Building Damage Pipeline: START...")

    # 1. download URL data
    download_main()

    # 2. build chip training datasets
    preprocess_main()

    # 3. merge training datasets (Palisades + Lahaina)
    prepare_dataset_main()

    # 4. train model & save metrics
    train_main()

    # 5. re-evaluate from saved model
    eval_main()

    # 6. run inference on Marshall wildfire area
    inference_main()

    logger.info("Completed SAR Building Damage Pipeline.")


if __name__ == "__main__":
    main()
