# quotientai Python Client

## Overview

`quotientai` is a SDK and CLI built to manage your workflows on Quotient AI, the AI Evaluation Company.

## Installation

**Prerequisites:**
- Python 3.10 or higher

**Setup Guide:**
1. Receive a token from your contace at Quotient AI.
2. Install `quotientai` client using pip:
   ```bash
   pip install git+https://{token}@github.com/quotient-ai/quotient-python.git@basic_cli
   ```

## Using `quotientai` from the Command Line



### Authentication
To use Quotient's platform, you'll need to create an account to Authenicate or use your organization's API Key (Coming Soon).

Authenticate your requests by setting environment variables for the email and password you want to register with:
```bash
export QUOTIENT_EMAIL='user@my_company.com';
export QUOTIENT_PASSWORD='my_secret_password';
```

### Registering your account

Create your `quotientai` account using the CLI:

```bash
quotient register user

Success! User has been registered!
Please check your email for a verification email before continuing.
```
**Note:** A verification email will be sent. Account verification is required to continue.



### Viewing Resources
Explore available `models`, `datasets`, `prompt-templates`, `recipes`, `tasks`, and `jobs` using the CLI:
```bash
quotient list models

+----+-----------------+-------------+------------------------------------------------+------------------+
| ID |       Name      |  Model Type |                  Description                   | Owner Profile ID |
+----+-----------------+-------------+------------------------------------------------+------------------+
| 1  | llama-2-7b-chat | HuggingFace |    a llama-2 model fine-tuned on chat data     |       N/A        |
| 2  |   mpt-7b-chat   | HuggingFace | a mpt model fine-tuned using the chatml format |       N/A        |
+----+-----------------+-------------+------------------------------------------------+------------------+
```

```bash
quotient list datasets

+----+-------------------+--------------+-------------------------------------------------------+-------------+-------+
| ID |        Name       | Dataset Type |                          URL                          | File Format | Owner |
+----+-------------------+--------------+-------------------------------------------------------+-------------+-------+
| 1  |      squad_v2     | HuggingFace  |                          N/A                          |     N/A     |  N/A  |
| 2  | summarize_dataset | RemoteSource | http://storage.googleapis.com/arize-assets/phoenix... |   parquet   |  N/A  |
+----+-------------------+--------------+-------------------------------------------------------+-------------+-------+
```

```bash
quotient list recipes

+-----------+-----------------+----------+-------------------------------------+--------------------+
| Recipe ID |    Model Name   | Model ID |         Prompt Template Name        | Prompt Template ID |
+-----------+-----------------+----------+-------------------------------------+--------------------+
|     1     | llama-2-7b-chat |    1     | Default Question Answering Template |         1          |
|     2     | llama-2-7b-chat |    1     |    Default Summarization Template   |         2          |
|     3     |   mpt-7b-chat   |    2     | Default Question Answering Template |         1          |
|     4     |   mpt-7b-chat   |    2     |    Default Summarization Template   |         2          |
+-----------+-----------------+----------+-------------------------------------+--------------------+
```

### Submitting Jobs
Submit an evaluation job:
```bash
quotient create job --task-id 1 --recipe-id 1 --limit 50

+----+---------+-----------+-----------+-------+------------------+
| ID | Task ID | Recipe ID |   Status  | Limit | Owner Profile ID |
+----+---------+-----------+-----------+-------+------------------+
| 67 |    1    |     1     | Scheduled |   50  |        3         |
+----+---------+-----------+-----------+-------+------------------+

```
Monitor job status:
```bash
quotient list jobs --filter id 67 # replace with your job ID

+----+---------+-----------+---------+-------+------------------+
| ID | Task ID | Recipe ID |  Status | Limit | Owner Profile ID |
+----+---------+-----------+---------+-------+------------------+
| 67 |    1    |     1     | Running |   50  |        3         |
+----+---------+-----------+---------+-------+------------------+
```

### Retrieving Results
When a job has completed, you can view the results:

```bash
quotient list results --job-id 67
+----+-----------------+-----------+------------------+--------------------+--------------+------+
| ID |    Model Name   | Task Name |     Metrics      |     Task Type      | Sample Count | Seed |
+----+-----------------+-----------+------------------+--------------------+--------------+------+
| 67 | llama-2-7b-chat |  squad-v2 | f1_score_jaccard | question_answering |      50      | N/A  |
+----+-----------------+-----------+------------------+--------------------+--------------+------+


+------------------------------+------------------------------+------------------------------+---------------------+
|           Question           |          Completion          |       Expected Answer        |     Metric Score    |
+------------------------------+------------------------------+------------------------------+---------------------+
| In what country is Norman... | Question: How much money ... |            France            |         0.0         |
| When were the Normans in ... | I have a question about t... | in the 10th and 11th cent... | 0.04210526315789474 |
| From which countries did ... |             None             | Denmark, Iceland and Norw... |         None        |
+------------------------------+------------------------------+------------------------------+---------------------+
More results available -- use the SDK to view them.
```

**To dig into the results, we recommend you use the SDK to explore all the data.**

## Using `quotientai` as a Python Package (SDK)

### Getting Started with the Python Client
Import and initialize the QuotientClient with your credentials:

```python
import os

from quotientai.client import QuotientClient

email = os.environ['QUOTIENT_EMAIL']
password = os.environ['QUOTIENT_PASSWORD']
client = QuotientClient(email, password)
```

### Register new user
To register for a new account programmatically:

```python
response = client.register(email, password)
```
**Note:** A verification email will be sent. Account verification is required to continue.

### Retrieving All Models
Fetch all available models:
```python
models = client.list_models()
```

### Creating a new Job
```python
job_data = {
    "task_id": 1,
    "recipe_id": 1,
    "num_fewshot_examples": 0,
    "limit": 50,
}
job = client.create_job(job_data)
```

### Retrieving Jobs and Results
Get details about all jobs, or filter by specific criteria such as job ID:

```python
jobs = client.list_jobs(filters={'id':job_id})
```

To explore your results data:

```python
results = client.get_eval_results(job_id)
```

## Support
For assistance and inquiries: [support@quotientai.co](mailto:support@quotientai.co)
