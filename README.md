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

## CLI Usage

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
Alternatively, pass credentials directly in commands:
```bash
quotient --email 'user@quotientai.co' --password 'my_secret_password' my-models  
```

### Viewing Resources
Explore available datasets, models, templates, tasks, recipes, and jobs using the CLI:
```bash
quotient my-models 
```
**Documentation:** For a comprehensive list of commands and features, visit our [Documentation](<Docs page URL>).

### Submitting Jobs
Submit an evaluation job:
```bash
quotient create-job --task-id 1 --recipe-id 1 # returns a new job object
```
Monitor job status:
```bash
quotient my-jobs --filter id 43 # replace with your job ID
```

## Support
For assistance and inquiries: [support@quotientai.co](mailto:support@quotientai.co)
