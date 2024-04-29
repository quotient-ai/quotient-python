import textwrap

from prettytable import PrettyTable


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


def format_metrics_table(data):
    table = PrettyTable()
    table.field_names = [
        "ID",
        "Name",
        "Owner",
    ]

    # Add row to the general table
    for metric_data in data:
        owner_id = (
            metric_data["owner_profile_id"]
            if metric_data["owner_profile_id"] is not None
            else "Open to all"
        )
        table.add_row(
            [
                metric_data["id"],
                metric_data["name"],
                owner_id,
            ]
        )
    return table
