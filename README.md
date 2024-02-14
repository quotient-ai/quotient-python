# quotient Python Client

## Overview

`quotient` is an SDK and CLI built to manage your workflows on Quotient AI, the AI Evaluation Company.

## Installation

**Prerequisites:**
- Python 3.10 or higher

**Setup Guide:**
1. Receive account information (email, password) from your contact at Quotient AI.

2. Install `quotient` client using pip:
   ```bash
   pip install git+https://{token}@github.com/quotient-ai/quotient-python.git
   ```

## Using `quotient` from the Command Line



### Authentication
To use Quotient's platform, you'll need to create an API key:
```bash
quotient authenticate --email <account_email>
```

Authenticate your requests by setting an environment variable for this API key:
```bash
export QUOTIENT_KEY=<api_key>;
```


### Registering your account

We are provisioning accounts until the open beta.



### Viewing Resources
Explore available `models`, `datasets`, `prompt-templates`, `recipes`, `tasks`, and `jobs` using the CLI:
```bash
quotient list models

+----+-----------------+-------------+------------------------------------------------+-------+
| ID |       Name      |  Model Type |                  Description                   | Owner |
+----+-----------------+-------------+------------------------------------------------+-------+
| 1  | llama-2-7b-chat | HuggingFace |    a llama-2 model fine-tuned on chat data     |  N/A  |
| 2  |   mpt-7b-chat   | HuggingFace | a mpt model fine-tuned using the chatml format |  N/A  |
+----+-----------------+-------------+------------------------------------------------+-------+
```

```bash
quotient list datasets

+----+-------------------+---------------------------+-------------+-------+
| ID |        Name       |            File           | File Format | Owner |
+----+-------------------+---------------------------+-------------+-------+
| 1  |      squad_v2     |            N/A            |     N/A     |  N/A  |
| 2  | summarize_dataset | llm_summarization.parquet |   parquet   |  N/A  |
+----+-------------------+---------------------------+-------------+-------+
```

```bash
quotient list recipes

+-----------+--------------------------+----------+-----------------+--------------------+-------------------------------------+
| Recipe ID |       Recipe Name        | Model ID |    Model Name   | Prompt Template ID |         Prompt Template Name        |
+-----------+--------------------------+----------+-----------------+--------------------+-------------------------------------+
|     1     | llama-question-answering |    1     | llama-2-7b-chat |         1          | Default Question Answering Template |
|     2     |   llama-summarization    |    1     | llama-2-7b-chat |         2          |    Default Summarization Template   |
|     3     |  mpt-question-answering  |    2     |   mpt-7b-chat   |         1          | Default Question Answering Template |
|     4     |    mpt-summarization     |    2     |   mpt-7b-chat   |         2          |    Default Summarization Template   |
+-----------+--------------------------+----------+-----------------+--------------------+-------------------------------------+
```

### Submitting Jobs
Submit an evaluation job:
```bash
quotient create job --task-id 1 --recipe-id 1 --limit 50

+----+---------+-----------+-----------+--------------------------+-----------+-------+-------+
| ID | Task ID | Task Name | Recipe ID |       Recipe Name        |   Status  | Limit | Owner |
+----+---------+-----------+-----------+--------------------------+-----------+-------+-------+
| 75 |    1    |  squad-v2 |     1     | llama-question-answering | Scheduled |   50  |   15  |
+----+---------+-----------+-----------+--------------------------+-----------+-------+-------+

```
Monitor job status:
```bash
quotient list jobs --filter id 75 # replace with your job ID

+----+---------+-----------+-----------+--------------------------+---------+-------+-------+
| ID | Task ID | Task Name | Recipe ID |       Recipe Name        |  Status | Limit | Owner |
+----+---------+-----------+-----------+--------------------------+---------+-------+-------+
| 75 |    1    |  squad-v2 |     1     | llama-question-answering | Running |   50  |   15  |
+----+---------+-----------+-----------+--------------------------+---------+-------+-------+
```

### Retrieving Results
When a job has completed, you can view the results:

```bash
quotient list results --job-id 75
+----+-----------------+-----------+------------------+--------------------+-----------+------+
| ID |    Model Name   | Task Name |     Metrics      |     Task Type      | # Samples | Seed |
+----+-----------------+-----------+------------------+--------------------+-----------+------+
| 75 | llama-2-7b-chat |  squad-v2 | f1_score_jaccard | question_answering |     46    | N/A  |
+----+-----------------+-----------+------------------+--------------------+-----------+------+
+------------------------------+------------------------------+------------------------------+----------------------+
|         Model Input          |         Model Output         |       Expected Answer        |     Metric Score     |
+------------------------------+------------------------------+------------------------------+----------------------+
| In what country is Norman... | Question: How much is the... |            France            |         0.0          |
| When were the Normans in ... | Your answers helped me un... |   10th and 11th centuries    | 0.05555555555555556  |
| From which countries did ... | The answer is not very cl... | Denmark, Iceland and Norw... | 0.06818181818181818  |
|  Who was the Norse leader?   | Question: Who was the lea... |            Rollo             | 0.04545454545454545  |
| What century did the Norm... | The answer is not difficu... | the first half of the 10t... | 0.027027027027027025 |
| Who gave their name to No... | Your answers helped me un... |         unanswerable         |         0.0          |
| What is France a region o... | Question: What is France ... |         unanswerable         |         0.0          |
| Who did King Charles III ... | Your answers helped me un... |         unanswerable         |         0.0          |
| When did the Frankish ide... | Question: When did the En... |         unanswerable         |         0.0          |
| Who was the duke in the b... | Question: How much money ... |    William the Conqueror     | 0.016949152542372885 |
| What is the original mean... | I have a question about t... |       Norseman, Viking       | 0.022988505747126436 |
| When was the Latin versio... | I have a question about t... |         9th century          |         0.0          |
| What name comes from the ... | I have a question about t... |         unanswerable         |         0.0          |
| When was the French versi... | I have a question about t... |         unanswerable         |         0.0          |
+------------------------------+------------------------------+------------------------------+----------------------+
More results available. Use the SDK to view more results
```

**To dig into the results, we recommend you use the SDK to explore all the data.**

## Using `quotientai` as a Python Package (SDK)

### Getting Started with the Python Client
Import and initialize the QuotientClient with your credentials:

```python
from quotientai.client import QuotientClient

client = QuotientClient()
```


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
results = client.get_eval_results(jobs[0]['id'])
for result in results['results']:
  print("Model Input:", result["content"]["input_text"])
  print("Model Output:", result["content"]["completion"])
  print("Expected Answer:", result["content"]["answer"])
  print("\n")
```

## Support
For assistance and inquiries: [support@quotientai.co](mailto:support@quotientai.co)
