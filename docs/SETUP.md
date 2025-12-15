# Detailed Setup & Execution Guide

## Prerequisites
- Git to store data files/repository & used for version control
- Docker Image
- Access to a Kubernetes cluster (Nautilus was used for this project)
- Python 3.10+

## Repository Structure
- src/ – all scripts
- kubernetes/ – Kubernetes Job YAML files
- data/ – dataset documentation
- results/ – outputs and metrics

## Repository Initialization and GitHub Integration
> This step can be skipped if Repo already exists.
1.  Initialize Git locally (if not already a repo):
```bash
cd /path/to/your-project
git init
git add -A
git commit -m "Initial commit"
```
Create a new repo on GitHub (web UI) and copy the SSH or HTTPS URL.

2. Add remote & push:
# SSH example
```bash
git remote add origin git@github.com:<your-username>/<repo>.git
git branch -M main
git push -u origin main
```

# or HTTPS example
```bash
git remote add origin https://github.com/<your-username>/<repo>.git
git branch -M main
git push -u origin main
```
3. Verify you can see the files on GitHub.

## Clone GitHub Repo into PVC via Kubernetes Pod
1. Create pod using pod.yaml
```bash
kubectl -n <namespace> create -f pod.yml
```
2. Clone Git Repo into Mounted PVC that lives within Pod
a. Exec into the running pod
```bash
kubectl -n <namespace> exec -it ecc7r-sar-project-pod -- /bin/bash
```
b. cd into project directory & clone
```bash
git clone <REPO-URL>
```
## High-Level Workflow
1. Apply PVC
```bash
kubectl apply -f kubernetes/pvc.yaml
```
2. Download the datasets from the URLs
```bash
kubectl apply -f kubernetes/job-download.yaml
```
3. Preprocess the data
```bash
kubectl apply -f kubernetes/job-preprocess.yaml
```
4. Train the model on the preprocessed data
```bash
kubectl apply -f kubernetes/job_train.yaml
```
**Special Note:** Throughout steps 1 through 4 and after applying the Kubernetes
Job YAML files, run the following commands to check the job status along the way.
```bash
kubectl get pods # check that the pod is running correctly
kubectl get jobs # check that the job is running
kubectl logs -f job/job-name-here
```
