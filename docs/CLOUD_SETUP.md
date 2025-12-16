# Nautilus-Specific Project Instructions

## Nautilus Cloud Platform Overview

- Cloud Platform: Nautilus
- Orchestration: Kubernetes
- Execution Model: Batch jobs
- Storage: PVC mounted at /data to ensure results exist after pod/job deletion
GPU Resources: NVIDIA GPUs allocated via Kubernetes resource requests

## Docker Image Information

A custom docker image was built, used, and pulled automatically at the 
start of each job. See Dockerfile for Docker Image details.
The docker image was hosted on the GitHub Container Registry:
ghcr.io/emcuttle/sar-damage:latest

## Namespace Information
All resources were deployed in the following Kubernetes namespace:
gp-engine-mizzou-dsa-cloud

## GPU Configuration
From job_train.yaml - 
```bash
resources:
  requests:
    cpu: "4"
    memory: "16Gi"
    nvidia.com/gpu: "1"
  limits:
    cpu: "4"
```bash
    memory: "19Gi"
    nvidia.com/gpu: "1"
