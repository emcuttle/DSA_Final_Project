# DSA Final Project Description
This repository contains files necessary for creating and traing a YOLO-based building damage
detection model using SAR imagery and deploying that model on the Nautilus cloud computing platform.
All python code files were created by Emily Cuttle, Will Lopez, Nic Alfaro, & Alexander (AJ) Knowles
as the final case study and capstone projects for the Data Science & Analytics Master's Program at 
the University of Missouri.

## How to Execute the Project on Nautilus
### Nautilus Account & PVC/data setup:
1. Change into the project folder/directory within Nautilus.
```
cd project_folder_name
```
2. In order to use the files in this repo, fork the GitHub repo via GitHub UI by navigating to this repo, 
   i.e. https://github.com/emcuttle/DSA_Final_Project 
  - Click Fork and choose your account
3. Execute either of the following commands within the Nautilus terminal
  - For SSH: git clone git@github.com:<your-username>/<forked-repo>.git
  - For HTTPS: git clone https://github.com/<your-username>/<forked-repo>.git 
3. Create a PVC and apply it to the cluster via the pvc.yaml file in the repo
```
kubectl apply -f kubernetes/pvc.yaml
```
4. Create a pod that mounts the PVC.
```
kubectl -n gp-engine-mizzou-dsa-cloud create -f pod.yml
```
5. Move into the running pod:
```
kubectl -n gp-engine-mizzou-dsa-cloud exec -it ecc7r-sar-project-pod-- /bin/bash
```
6. Create the directory/folder where you want the data to go and then move into it
```
mkdir project_folder_name
cd project1_folder_name
```
7. Clone the git repo into the mounted PVC within that is now accessible within the pod
```
git clone https://github.com/emcuttle/DSA_Final_Project
```
9. exit the pod and delete it
```
exit
kubectl delete pod ecc7r-sar-project-pod -n gp-engine-mizzou-dsa-cloud
```

### Execute Kubernetes Jobs
Execute Kubernetes Jobs in this sequence:
    1. job-download.yaml
    2. job_preprocess.yaml
    3. job_train.yaml
Execute the following commands for every job:
  1. Change into the project folder/directory within Nautilus.
     ```
     cd project1
     ```
  2. Create the Kubernetes job using the YAML file.
     ```
     kubectl apply -f kubernetes/job_file_name.yaml
     ```
  3. Check the status of the job: Running means the job is in progress, Failed indicates an error,
     and Complete means the job was completed.
     ```
    kubectl get jobs
    ```
  4. Check the status of the pod: ContainerCreating means the container for the job is currently being
     created, Running means the container has been successfully created and the job is in progress, Error
     indicates an error, and Completed means the job was completed.
     ```
     kubectl get pods
     ```
  5. Check the status of the job by pulling the job logs.
     ```
     kubectl logs -f job/job/pod-name
     ```
  6. Once the status of the Job is “Complete”, delete the job.
     ```
     kubectl delete job sar-train-job
     ```

# Exercise 6 – Validating Data Source URLs - Kubernetes Job

This Kubernetes Job performs validation of dataset URLs for my final project, SAR Wildfire Building Damage Detection Model. 
It prints the dataset URLs, extracts the filenames, and confirms that the inputs are correctly formatted.

To run the job in Nautilus:
```bash
kubectl apply -f exercise6_data_loading_job.yaml
```

**Special Note:** AI-assisted tools were used for initial project brainstorming, suggesting improvements to document and code
writing, and debugging; all experiments and results were executed by the author.
