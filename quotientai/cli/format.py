from prettytable import PrettyTable
import textwrap

def print_pretty_models_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Model Type", "Description", "Owner"]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        table.add_row(
            [
                item["id"],
                item["name"],
                item["model_type"],
                item["description"],
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
    return '\n'.join(textwrap.wrap(text, max_width))


def print_pretty_prompt_template_table(data):
    table = PrettyTable()
    table.field_names = ["ID", "Name", "Template String", "Owner"]

    # Add rows to the table
    for item in data:
        owner_id = (
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        sanitized_template = sanitize_string(item["template_string"])
        table.add_row([item["id"], item["name"], sanitized_template, owner_id])

    return table


def print_pretty_recipes_table(data):
    table = PrettyTable()
    table.field_names = [
        "Recipe ID",
        "Recipe Name",
        "Model ID",
        "Model Name",
        "Prompt Template ID",
        "Prompt Template Name",
        "Owner"
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
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        table.add_row(
            [
                recipe_id,
                recipe_name,
                model_id,
                model_name,
                prompt_template_id,
                prompt_template_name,
                owner_id
            ]
        )

    return table


def print_pretty_jobs_table(data):
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


def print_pretty_datasets_table(data):
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
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        table.add_row([id, name, url, file_format, owner])

    return table


def print_pretty_tasks_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Task Name",
        "Dataset ID",
        "Dataset Name",
        "Task Type",
        "Metrics",
        "Owner",
    ]

    # Add rows to the table
    for item in data:
        id = item["id"]
        task_name = item["name"]
        dataset_id = item["dataset_id"]
        dataset_name = item["dataset_name"]
        task_type = item["task_type"]
        metrics = item["metrics"]
        owner = (
            item["owner_profile_id"] if item["owner_profile_id"] is not None else "N/A"
        )
        table.add_row(
            [id, task_name, dataset_id, dataset_name, task_type, metrics, owner]
        )

    return table


def print_pretty_results_summary_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Model Name",
        "Task Name",
        "Metrics",
        "Task Type",
        "# Samples",
        "Seed",
    ]

    # Add row to the general table
    metrics = ", ".join(data["metrics"])
    seed = data["seed"] if data["seed"] is not None else "N/A"
    table.add_row(
        [
            data["id"],
            data["model_name"],
            data["task_name"],
            metrics,
            data["task_type"],
            len(data["results"]),
            seed,
        ]
    )
    return table


def print_pretty_results_table(data):
    table = PrettyTable()
    table.field_names = [
        "Model Input",
        "Model Output",
        "Expected Answer",
        "Metric Score",
    ]

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
        metric_score = result["value"]
        table.add_row([question, completion, expected_answer, metric_score])

    has_more_results = len(data["results"]) > table_length

    return table, has_more_results
