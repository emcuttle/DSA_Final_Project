# Results Summary

## Model Training Execution

- Platform: Nautilus
- Execution Mode: Kubernetes batch job
- GPU: NVIDIA GPU allocated via Kubernetes
- Dataset Used: Palisades Wildfire data - building footprint data and wildfire SAR imagery
- Model: YOLOv8

## Model Performance

- Top-1 Accuracy: ~0.82
- Top-5 Accuracy: 1.00

**Special Note:** Detailed model metrics in metrics.json

## Generated Artifacts
1. Trained model weights:  
  `models/building_damage_classifier_best.pt`

2. Evaluation metrics:  
  `results/metrics.json`

3.  Job execution logs:  
  `results/execution_log.txt`
