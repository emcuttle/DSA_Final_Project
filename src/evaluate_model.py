import os
import json
import logging
from ultralytics import YOLO

from utils import DATASETS_DIR, MODELS_DIR, RESULTS_DIR
from train_model import compute_classification_metrics

logger = logging.getLogger("evaluate_model")


def main():
    dataset_dir = os.path.join(DATASETS_DIR, "building_dataset")
    model_path = os.path.join(MODELS_DIR, "building_damage_classifier_best.pt")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Trained model not found at {model_path}."
        )

    logger.info("Evaluating saved model on test split...")
    model = YOLO(model_path)
    metrics = model.val(data=dataset_dir, split="test")
    metrics_dict = compute_classification_metrics(metrics, model)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    metrics_path = os.path.join(RESULTS_DIR, "metrics_eval.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)

    logger.info(f"Saved evaluation metrics to: {metrics_path}")
    logger.info("Evaluation complete.")


if __name__ == "__main__":
    main()
