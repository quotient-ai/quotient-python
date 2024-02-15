import ast
import json
import logging
import mimetypes
import os
import time
from datetime import datetime

logging.basicConfig(level=logging.WARNING)

import requests
from postgrest import APIError
from quotientai.exceptions import (
    QuotientAIAuthException,
    QuotientAIInvalidInputException,
)

from supabase import create_client


class QuotientClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

        # Public API key for the QuotientAI Supabase project
        self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhocXBwY3FsdGtsemZwZ2dkb2NiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDEzNTU4MzgsImV4cCI6MjAxNjkzMTgzOH0.bpOtVl7co6B4wXQqt6Ec-WCz9FuO7tpVYbTa6PLoheI"
        self.supabase_url = "https://hhqppcqltklzfpggdocb.supabase.co"
        self.supabase_client = create_client(self.supabase_url, self.public_api_key)

        # Eval Scheduler config
        self.eval_scheduler_url = (
            "http://eval-scheduler-alb-887401167.us-east-2.elb.amazonaws.com"
        )

        # Client Auth Token
        self.token = None
        self.token_expiry = 0

    def register_user(self):
        response = self.supabase_client.auth.sign_up(
            {
                "email": self.email,
                "password": self.password,
            }
        )

        if response and hasattr(response, "user"):
            print(f"Success! {self.email} has been registered!")

            if response.user.confirmed_at is None:
                print(
                    "Please check your inbox and verify your email before continuing."
                )

        return response

    def login_to_supabase(self):
        response = self.supabase_client.auth.sign_in_with_password(
            {"email": self.email, "password": self.password}
        )
        session = response.session
        self.supabase_client.postgrest.auth(token=session.access_token)
        self.token = response.session.access_token
        self.token_expiry = (
            time.time() + response.session.expires_in - 60
        )  # 60 seconds buffer

    def sign_out(self):
        self.supabase_client.auth.sign_out()
        self.token = None
        self.token_expiry = 0

    def check_token(self):
        current_time = time.time()
        if not self.token or current_time >= self.token_expiry:
            self.login_to_supabase()

    ###########################
    #         Models          #
    ###########################

    def list_models(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("model").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    ###########################
    #     Prompt Templates    #
    ###########################

    def list_prompt_templates(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("prompt_template").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_prompt_template(self, template, name):
        self.check_token()

        endpoint = "create-prompt-template"
        url = f"{self.eval_scheduler_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        response = requests.post(
            url, headers=headers, params={"template": template, "name": name}
        )

        if response.status_code != 200:
            raise QuotientAIInvalidInputException(
                f"Failed to create prompt template for reason: {response.json()['detail']}"
            )
        return response.json()

    def delete_prompt_template(self, template_id):
        self.check_token()
        query = (
            self.supabase_client.table("prompt_template").delete().eq("id", template_id)
        )
        try:
            response = query.execute()
        except APIError as e:
            raise QuotientAIAuthException(
                f"Failed to delete prompt template with id {template_id}. Resource is still in use."
            )
        if not response.data:
            raise QuotientAIAuthException(
                f"Failed to delete prompt template with id {template_id}. Does not exist or unauthorized."
            )
        return response.data

    ###########################
    #         Recipes         #
    ###########################

    def list_recipes(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("recipe").select(
            "*,prompt_template(*),model(*)"
        )
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_recipe(
        self,
        model_id: int,
        prompt_template_id: int,
        name: str = None,
        description: str = None,
    ):
        self.check_token()

        recipe = {"model_id": model_id, "prompt_template_id": prompt_template_id}
        recipe.update({"created_at": datetime.utcnow().isoformat()})
        if name:
            recipe.update({"name": name})
        if description:
            recipe.update({"description": description})
        query = self.supabase_client.table("recipe").insert(recipe)
        try:
            response = query.execute()
        except APIError as e:
            # print(e.args[0])
            # error_data = json.loads(e.args[0])
            error_data = ast.literal_eval(e.args[0])
            error_code = error_data["code"]
            if error_code == "42501":
                raise QuotientAIInvalidInputException(
                    "Failed to create recipe. Violated row-level security policy for table."
                )
            else:
                raise QuotientAIInvalidInputException(
                    f"Failed to create recipe. Error code: {error_code}"
                )

        recipe_response = response.data[0]
        recipe_id = recipe_response["id"]
        # Supabase does not support returning nested objects, so we need to
        # manually fetch the prompt template and model after create
        return self.list_recipes({"id": recipe_id})[0]

    ###########################
    #         Datasets        #
    ###########################

    def list_datasets(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("dataset").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_dataset(self, file_path: str, name: str):
        self.check_token()

        endpoint = "upload-dataset"
        url = f"{self.eval_scheduler_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        # Client side file size check
        size_threshold = 2 * 1024 ** 3  # 2GB
        file_size = os.path.getsize(file_path)
        if file_size > size_threshold:
            raise QuotientAIInvalidInputException(
                "File size exceeds 2GB limit"
            )

        # Guess the MIME type of the file
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            raise Exception("Could not determine the file's MIME type")

        file_name = os.path.basename(file_path)
        params = {
            "name": name,
        }
        files = {"file": (file_name, open(file_path, "rb"), mime_type)}

        try:
            response = requests.post(url, headers=headers, params=params, files=files)
            response.raise_for_status()
            dataset_id = response.json()["id"]
            return self.list_datasets({"id": dataset_id})[0]
        except requests.RequestException as e:
            raise Exception(f"Failed to upload dataset: {e}")
        finally:
            files["file"][1].close()

    ###########################
    #          Tasks          #
    ###########################

    def list_tasks(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("task").select("*,dataset(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    ###########################
    #          Jobs           #
    ###########################

    def list_jobs(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("job").select("*,task(*),recipe(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_job(self, task_id, recipe_id, num_fewshot_examples, limit):
        self.check_token()
        job_data = {
            "task_id": task_id,
            "recipe_id": recipe_id,
            "num_fewshot_examples": num_fewshot_examples,
            "limit": limit,
        }
        job_data.update({"status": "Scheduled"})
        job_data.update({"created_at": datetime.utcnow().isoformat()})
        query = self.supabase_client.table("job").insert(job_data)
        response = query.execute()
        job = response.data[0]
        job_id = job["id"]
        # Supabase does not support returning nested objects, so we need to
        # manually fetch the task and recipe after create
        return self.list_jobs({"id": job_id})[0]

    def get_eval_results(self, job_id):
        self.check_token()

        endpoint = "get-eval-results"
        url = f"{self.eval_scheduler_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, params={"job_id": job_id})

        if response.status_code == 200:
            return response.json()
        else:
            return f"Failed with status code: {response.status_code}"
