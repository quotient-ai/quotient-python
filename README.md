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
More results available. Use the SDK to view more results
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

### Sign Up
To sign up for a new account programmatically:

```python
client.sign_up(email, password)
```
**Note:** A verification email will be sent. Account verification is required to continue.

### Retrieving All Models
Fetch all available models:
```python
client.list_models()
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

### Retrieving Jobs ad Results
Get details about all jobs, or filter by specific criteria like job ID:

```python
client.list_jobs(filters={'id':<your job id>})
```

To explore your results data:

```python
client.get_eval_results(<your job id>)
```

## Support
For assistance and inquiries: [support@quotientai.co](mailto:support@quotientai.co)
