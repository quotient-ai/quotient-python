import json
import os
import textwrap
import time

import pandas as pd
from prettytable import PrettyTable
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn


def format_api_keys_table(data):
    table = PrettyTable()
    table.field_names = ["Name", "Revoked", "Created At", "Expires At"]
    for item in data:
        table.add_row(
            [
                item["key_name"],
                item["revoked"],
                item["created_at"],
                item["expires_at"],
            ]
        )
    return table


def format_models_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Provider", "Owner"]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        provider = item["model_type"]
        table.add_row(
            [
                item["id"],
                item["name"],
                provider,
                owner_id,
            ]
        )

    return table


def sanitize_string(input_string, max_width=40):
    # Replace newlines and other special characters for display
    sanitized = input_string.replace("\\n", "\n").replace("\\t", "\t")
    return wrap_text(sanitized, max_width)


def truncate_string(input_string, max_length=50):
    # Truncate the string to a maximum length with ellipsis
    return (
        (input_string[:max_length] + "...")
        if len(input_string) > max_length
        else input_string
    )


def select_file_name_from_url(url):
    # Select the file name from a URL
    return url.split("/")[-1]


def wrap_text(text, max_width):
    return "\n".join(textwrap.wrap(text, max_width))


def format_system_prompt_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Message String", "Owner"]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        sanitized_template = sanitize_string(item["message_string"])
        table.add_row([item["id"], item["name"], sanitized_template, owner_id])

    return table


def format_prompt_template_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Template String", "Owner"]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        sanitized_template = sanitize_string(item["template_string"])
        table.add_row([item["id"], item["name"], sanitized_template, owner_id])

    return table


def format_recipes_table(data):
    table = PrettyTable()
    table.field_names = [
        "Recipe ID",
        "Recipe Name",
        "Model ID",
        "Model Name",
        "Prompt Template ID",
        "Prompt Template Name",
        "Owner",
    ]

    # Add rows to the table
    for item in data:
        recipe_id = item["id"]
        recipe_name = item["name"]
        model_id = item["model"]["id"]
        model_name = item["model"]["name"]
        prompt_template_id = item["prompt_template"]["id"]
        prompt_template_name = item["prompt_template"]["name"]
        owner_id = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        table.add_row(
            [
                recipe_id,
                recipe_name,
                model_id,
                model_name,
                prompt_template_id,
                prompt_template_name,
                owner_id,
            ]
        )

    return table


def format_jobs_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Task ID",
        "Task Name",
        "Recipe ID",
        "Recipe Name",
        "Status",
        "Limit",
        "Owner",
    ]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        table.add_row(
            [
                item["id"],
                item["task_id"],
                item["task"]["name"],
                item["recipe_id"],
                item["recipe"]["name"],
                item["status"],
                item["limit"],
                owner_id,
            ]
        )

    return table


def format_datasets_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "File", "File Format", "Owner"]

    # Add rows to the table
    for item in data:
        id = item["id"]
        name = item["name"]
        dataset_type = item["dataset_type"]
        url = (
            truncate_string(select_file_name_from_url(item["url"]))
            if item["url"] is not None
            else "N/A"
        )
        file_format = item["file_format"] if item["file_format"] is not None else "N/A"
        owner = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        table.add_row([id, name, url, file_format, owner])

    return table


def format_tasks_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Task Name",
        "Dataset ID",
        "Task Type",
        "Owner",
    ]

    # Add rows to the table
    for item in data:
        id = item["id"]
        task_name = item["name"]
        dataset_id = item["dataset_id"]
        task_type = item["task_type"]
        owner = (
            item["owner_profile_id"]
            if item["owner_profile_id"] is not None
            else "Open to all"
        )
        table.add_row([id, task_name, dataset_id, task_type, owner])

    return table


def format_results_summary_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Model Name",
        "Task Name",
        "Task Type",
        "# Samples",
        "Seed",
    ]

    # Add row to the general table
    seed = data["seed"] if data["seed"] is not None else "N/A"
    table.add_row(
        [
            data["id"],
            data["model_name"],
            data["task_name"],
            data["task_type"],
            len(data["results"]),
            seed,
        ]
    )
    return table


def format_results_table(data):
    table = PrettyTable()
    table.field_names = ["Model Input", "Model Output", "Expected Answer"]

    table_length = 20
    cell_char_limit = 25

    # Add rows to the results table
    for result in data["results"][
        :table_length
    ]:  # Limit to first <table_length> results
        question = (
            truncate_string(result["content"]["input_text"], cell_char_limit)
            if isinstance(result["content"]["input_text"], str)
            else result["content"]["input_text"]
        )
        completion = (
            truncate_string(result["content"]["completion"], cell_char_limit)
            if isinstance(result["content"]["completion"], str)
            else result["content"]["completion"]
        )
        expected_answer = (
            truncate_string(result["content"]["answer"], cell_char_limit)
            if isinstance(result["content"]["answer"], str)
            else result["content"]["answer"]
        )
        table.add_row([question, completion, expected_answer])

    has_more_results = len(data["results"]) > table_length

    return table, has_more_results


def save_results_to_file(data):
    data_to_frame = []
    for item in data["results"]:
        content = item["content"]
        row = {
            "id": content["id"],
            "input_text": content["input_text"],
            "answer": content["answer"],
            "completion": content["completion"],
            "context": content["context"],
            "formatted_content": content["formatted_content"],
        }
        data_to_frame.append(row)

    df = pd.DataFrame(data_to_frame)
    file_name = f"quotient-results-{data['id']}.csv"
    df.to_csv(file_name, index=False)
    full_path = os.path.abspath(file_name)
    print(f"Results saved to {full_path}")


def save_metrics_to_file(data):
    df = pd.json_normalize(data, "results")
    df = df[df.columns[df.columns.str.contains("metric")]]
    df.columns = df.columns.str.replace("metric.", "")
    description = df.describe()
    file_name = f"quotient-metrics-{data['id']}.csv"
    description.to_csv(file_name, index=False)
    full_path = os.path.abspath(file_name)
    print(f"Metrics saved to {full_path}")


def save_eval_metadata_to_file(data):
    selected_info = {
        "model_name": data.get("model_name"),
        "task_name": data.get("task_name"),
        "completed_at": data.get("completed_at"),
        "id": data.get("id"),
        "task_type": data.get("task_type"),
        "seed": data.get("seed"),
    }

    file_name = f"quotient-eval-metadata-{data['id']}.json"
    with open(file_name, "w") as json_file:
        json.dump(selected_info, json_file, indent=4)
    full_path = os.path.abspath(file_name)
    print(f"Evaluation metadata saved to {full_path}")


def monitor_job_progress(client, job_id):
    console = Console()
    job_progress_data = client.list_job_progress(job_id)
    job_data = client.list_jobs({"id": job_id})
    job_status = job_data[0]["status"]

    if not job_data:
        print("Job not found.")
        return

    if job_status == "Scheduled":
        with console.status("Waiting for Job to start...", spinner="dots", speed=1):
            while job_status == "Scheduled":
                job_data = client.list_jobs({"id": job_id})
                job_status = job_data[0]["status"]
                time.sleep(2)

    if job_status == "Failed":
        print("Job failed. No progress to report.")
        return
    if job_status == "Completed":
        print("Job completed!")
        return

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.fields[parallel]}"),
        console=console,
    ) as progress:
        inference_task = progress.add_task(
            "[cyan]Inference Progress",
            total=get_total_chunks(job_progress_data, "Inference"),
            parallel="Parallelization: 0",
        )
        metrics_task = progress.add_task(
            "[green]Metrics Progress",
            total=get_total_chunks(job_progress_data, "Metrics"),
            parallel="Parallelization: 0",
        )
        job_complete = False

        while not job_complete:
            job_progress_data = client.list_job_progress(job_id)
            job_complete = update_progress(
                progress, job_progress_data, inference_task, metrics_task
            )
            time.sleep(2)
        print("Job completed!")


def update_progress(progress, data, inference_task, metrics_task):
    """Updates the progress bars and parallelization text."""
    (
        completed_inference,
        total_inference,
        parallelization_inference,
    ) = get_progress_and_parallelization(data, "Inference")
    (
        completed_metrics,
        total_metrics,
        parallelization_metrics,
    ) = get_progress_and_parallelization(data, "Metrics")

    progress.update(
        inference_task,
        completed=completed_inference,
        total=total_inference,
        parallel=f"Parallelization: {parallelization_inference}",
    )
    progress.update(
        metrics_task,
        completed=completed_metrics,
        total=total_metrics,
        parallel=f"Parallelization: {parallelization_metrics}",
    )

    return (
        completed_inference == total_inference
        and completed_metrics == total_metrics
        and completed_inference > 0
        and completed_metrics > 0
    )


def get_progress_and_parallelization(data, job_step):
    """Calculates and returns the number of completed chunks, total chunks, and current parallelization for a given job step."""
    progress_trackers = [x for x in data if x["job_step"] == job_step]
    current_parallelization = [x for x in progress_trackers if x["finished_at"] is None]

    completed = len(progress_trackers) - len(current_parallelization)
    total_chunks = get_total_chunks(data, job_step)
    return completed, total_chunks, len(current_parallelization)


def get_total_chunks(data, job_step):
    """Returns the total chunks for a given job step."""
    trackers = [x for x in data if x["job_step"] == job_step]
    if trackers:
        return trackers[0]["total_chunks"]
    return 0
