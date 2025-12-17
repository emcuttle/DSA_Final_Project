**Specific Tools Used:** OpenAI ChatGPT (GPT-4 / GPT-5 family)

**Purpose of Use**: Used throughout the final project. This includes brainstorming and planning the project workflow, 
suggesting improvements for writing YAML files, Github files, and code that could be successfully deployed on Nautilus, 
and assistance with debugging Nautilus errors.

**Prompts/Queries (Representative):**
1.	I am working on a final project where I am building a SAR-based building damage detection model from wildfires. The project
  will be deployed on the Nautilus cloud platform using Docker and Kubernetes. Can you help me brainstorm a workflow for this project?
2.	I am writing a Kubernetes job YAML file to run my model on Nautilus, but I want to make sure I am creating it successfully – 
  resources, structure, etc. Can you review a typical job YAML setup and tell me best practices for running this type of model on Nautilus?
3.	I ran the training job on Nautilus and the pod was created and started running, but after a little while the logs stop updating. 
    I also don’t see an error. What are some possible reasons this might be happening and how can I fix it?

**AI Responses:**
1.	A clear end-to-end workflow will help both with implementation and with explaining your project in the final report. One logical way 
    to structure your workflow is as follows:
  a.	Data acquisition: Collect all required datasets, including SAR imagery for wildfire events (such as Palisades and Lahaina) and building 
    footprint vector data. Ensure all data sources are documented and stored in a structured directory (e.g., raw data folder).
  b.	Data preprocessing: Prepare SAR imagery by clipping it to the area of interest, normalizing pixel values, and aligning spatial resolution 
    as needed. For building footprints, clean geometries, project to a common coordinate reference system, and label buildings based on damage 
      information if available.
  c.	Dataset preparation: Combine SAR image patches with corresponding building footprint labels to create a training dataset. Split the dataset 
      into training, validation, and testing subsets, ensuring consistent class distributions.
  d.	Model development and training: Implement a computer vision model (such as a YOLO-based architecture) that takes SAR image inputs and predicts 
        building damage classes. Train the model using the prepared dataset and track metrics such as accuracy, precision, recall, and loss.
  e.	Containerization: Package the code, dependencies, and model into a Docker image. Ensure the image can be run non-interactively and supports 
    GPU acceleration if required.
  f.	Cloud deployment: Deploy the Docker image to Nautilus using Kubernetes job YAML files. Specify appropriate CPU, memory, and GPU resources 
    based on model requirements.
  g.	Model evaluation and inference: Run inference on unseen wildfire data to assess generalization performance. Store outputs and logs for later analysis.
This workflow provides a clear narrative from raw data to an operational product and aligns well with cloud-based execution requirements.

2.	When running deep learning workloads on Nautilus, your Kubernetes job YAML should clearly define resource requests, limits, and execution
   behavior. Some best practices to consider include:
  a.	Explicit resource requests and limits: Always specify CPU, memory, and GPU requests to avoid over-allocation or scheduling delays. For example,
request only the number of GPUs required by your model and ensure memory limits are sufficient for loading SAR imagery.
  b.	Use batch jobs for training: A Kubernetes Job is appropriate for training and inference tasks that run to completion. Set restartPolicy:
Never to prevent unintended restarts.
  c.	Persistent storage: Mount a Persistent Volume Claim (PVC) to store datasets and model outputs so results persist after the job finishes.
  d.	Environment configuration: Define environment variables for paths, model parameters, or configuration files to keep your code flexible and reusable.
  e.	Logging and observability: Ensure your application writes logs to stdout/stderr so they can be accessed using kubectl logs. This is essential
for debugging stalled jobs.
  f.	Avoid unnecessary privileges: Use the default service account unless elevated permissions are required.
Structuring your YAML this way improves reproducibility, makes debugging easier, and aligns with how Nautilus schedules GPU-enabled workloads.

3.	If your pod starts successfully but appears to stall, there are several common causes to investigate:
  a.	Resource starvation or scheduling issues: Even if the pod starts, the node may not have sufficient available resources to execute the workload
effectively. Check the node assignment and confirm that requested resources match what is available.
  b.	Application-level blocking: The code may be waiting on a blocking operation such as data loading, file I/O, or a deadlocked process. Adding logging
statements before and after major steps can help identify where execution stops.
  c.	Batch size or memory constraints: Deep learning workloads can silently fail or hang if the batch size is too large for available GPU memory. Reducing the batch
size is a common first troubleshooting step.
  d.	Data access problems: If the pod cannot access mounted volumes or required files, it may hang while attempting retries. Verify that the PVC is correctly mounted
and paths are correct.
  e.	GPU initialization issues: Ensure that the container image supports CUDA and that the GPU is visible inside the container by checking environment variables
and device availability.
To troubleshoot, use kubectl describe pod to inspect events, check logs frequently, reduce batch size, and simplify the workload to isolate the failing component.

**My Process:** 
After reading the AI responses, I started to create or troubleshoot whatever it was I was trying to do whether that be project planning, writing YAML files, 
debugging Nautilus errors, etc. I had to tailor what AI suggested to fit my specific project and needs and ask any follow up questions if I didn’t understand 
anything in AI’s responses. The project was fully executed by me and decisions on paths forward were also made by me, but AI was used as a tool/aid in the 
cases listed above throughout the project.
