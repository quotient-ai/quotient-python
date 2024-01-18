# quotientai Python Client

## Overview

The `quotientai` Python client is an advanced tool for managing evaluation workflows for your AI Models and Evaluation Tasks.

## Installation


**Prerequisites:**
- SSH keys added to GitHub
- Access to the private `quotient-ai` package repository
- Python 3.10 or higher

**Setup Guide:**
1. Ensure your SSH keys are added to GitHub ([SSH Key Setup Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)).
2. Install `quotientai` client using pip:
   ```bash
   pip install git+ssh://git@github.com/quotient-ai/quotient-python.git@basic_cli
   ```

## Using `quotientai` from the Command Line

### Signing Up
Create your `quotientai` account using the CLI:

```bash
quotient sign-up --email 'user@quotientai.co' --password 'my_secret_password'
```
**Note:** A verification email will be sent. Account verification is required to continue.

### Authentication
Authenticate your requests by setting environment variables:
```bash
export QUOTIENT_EMAIL='user@quotientai.co';
export QUOTIENT_PASSWORD='my_secret_password';
```

### Viewing Resources
Explore available datasets, models, templates, tasks, recipes, and jobs using the CLI:
```bash
quotient list models
```
**Documentation:** For a comprehensive list of commands and features, visit our [Documentation](<Docs page URL>).

### Submitting Jobs
Submit an evaluation job:
```bash
quotient create job --task-id 1 --recipe-id 1 # returns a new job object
```
Monitor job status:
```bash
quotient list jobs --filter id 43 # replace with your job ID
```

## Using `quotientai` as a Python Package

### Getting Started with the Python Client
Import and initialize the QuotientClient with your credentials:

```python
import os

from quotientai.client import QuotientClient

email = os.environ['QUOTIENT_EMAIL']
password = os.environ['QUOTIENT_PASSWORD']
client = QuotientClient(email, password)

### Sign Up
To sign up for a new account programmatically:

```python
client.sign_up(email, password)
```
**Note:** A verification email will be sent. Account verification is required to continue.

### Retrieving All Models
Fetch all available models:
```python
client.get_all_models()
```

### Creating a new Job
```python
job_data = {
    "task_id": 1,
    "recipe_id": 1,
    "num_fewshot_examples": 0,
    "limit": 50,
}
client.create_job(job_data)
```

### Retrieving Jobs
Get details about all jobs, or filter by specific criteria like job ID:

```python
client.get_all_jobs(filters={'id':44})
```
## Support
For assistance and inquiries: [support@quotientai.co](mailto:support@quotientai.co)
