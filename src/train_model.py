import os
import json
import logging
import numpy as np
from ultralytics import YOLO

from utils import DATASETS_DIR, MODELS_DIR, RESULTS_DIR

logger = logging.getLogger("train_model")


def compute_classification_metrics(metrics, model):
    """
    Calucluate the following metrics for the model:
    precision, recall, F1 per class and macro averages.
    """
    conf_matrix = metrics.confusion_matrix.matrix
    conf_matrix = conf_matrix[:2, :2]

    tp = np.diag(conf_matrix)
    fp = np.sum(conf_matrix, axis=0) - tp
    fn = np.sum(conf_matrix, axis=1) - tp

    eps = 1e-7
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    f1 = 2 * (precision * recall) / (precision + recall + eps)

    class_names = list(model.names.values())
    per_class = {}
    for i, class_name in enumerate(class_names[:2]):
        per_class[class_name] = {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
        }

    metrics_dict = {
        "top1_accuracy": float(metrics.top1),
        "top5_accuracy": float(metrics.top5),
        "per_class": per_class,
        "macro_precision": float(np.mean(precision)),
        "macro_recall": float(np.mean(recall)),
        "macro_f1": float(np.mean(f1)),
    }
    return metrics_dict


def main():
    dataset_dir = os.environ.get("DATASET_DIR", "/data/datasets/palisades_building_dataset")
    if not os.path.isdir(dataset_dir):
        raise FileNotFoundError(dataset_dir)

    logger.info("Training YOLOv8 classification model...")
    model = YOLO("yolov8l-cls.pt")

    results = model.train(
        data=dataset_dir,
        epochs=50,
        imgsz=256,
        patience=10,
        batch=32,
        name="building_damage_classifier",
    )

    logger.info("Training complete.")

    # get path to best weights
    runs_dir = "runs/classify/building_damage_classifier"
    best_weights = os.path.join(runs_dir, "weights", "best.pt")

    os.makedirs(MODELS_DIR, exist_ok=True)
    final_model_path = os.path.join(MODELS_DIR, "building_damage_classifier_best.pt")

    if os.path.exists(best_weights):
        import shutil

        shutil.copy2(best_weights, final_model_path)
        logger.info(f"Copied best model to: {final_model_path}")
    else:
        logger.warning("Could not find best weights.")

    logger.info("Evaluating model on test split...")
    metrics = model.val(data=dataset_dir, split="test")
    metrics_dict = compute_classification_metrics(metrics, model)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    metrics_path = os.path.join(RESULTS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)

    logger.info(f"Saved metrics to: {metrics_path}")


if __name__ == "__main__":
    main()
