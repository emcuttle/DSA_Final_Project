# DSA_Final_Project
Final project for University of Missouri's Data Science &amp; Analytics Masters program.


# Exercise 6 – Validating Data Source URLs - Kubernetes Job

This Kubernetes Job performs validation of dataset URLs for my final project, SAR Wildfire Building Damage Detection Model. 
It prints the dataset URLs, extracts the filenames, and confirms that the inputs are correctly formatted.

To run the job in Nautilus:
```bash
kubectl apply -f exercise6_data_loading_job.yaml
