import os
import time

import pandas as pd
from rich.console import Console
from rich.progress import Progress


def show_job_progress(client, job_id):
    console = Console()
    job_progress_data = client.list_job_progress(job_id)
    job_data = client.list_jobs({"id": job_id})
    job_status = job_data[0]["status"]

    if not job_data:
        print("Job not found.")
        return

    if job_status == "Scheduled":
        with console.status(
            "Waiting for Job to start...", spinner="aesthetic", speed=0.5
        ):
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

    total_chunks = get_total_chunks(job_progress_data, "Inference")

    with Progress() as progress:
        inference_task = progress.add_task(
            "[cyan]Getting Completions...",
            total=total_chunks,
        )
        metrics_task = progress.add_task(
            "[green]Computing Metrics...",
            total=total_chunks,
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
        inference_task, completed=completed_inference, total=total_inference
    )
    progress.update(metrics_task, completed=completed_metrics, total=total_metrics)

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


def results_to_dataframe(data):
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

    metrics_df = pd.json_normalize(data["results"])
    # Select only columns that have "metric" in their header and clean the column names
    metrics_df = metrics_df[
        metrics_df.columns[metrics_df.columns.str.contains("metric")]
    ]
    metrics_df.columns = metrics_df.columns.str.replace("metric.", "")
    full_df = df.join(metrics_df)

    return full_df


def results_to_csv(data):
    df = results_to_dataframe(data)
    file_name = f"quotient-results-{data['id']}.csv"
    df.to_csv(file_name, index=False)
    full_path = os.path.abspath(file_name)
    print(f"Results saved to {full_path}")
    return full_path
