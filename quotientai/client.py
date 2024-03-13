import ast
import logging
import mimetypes
import os
import time
from datetime import datetime

logging.basicConfig(level=logging.WARNING)

import requests
from quotientai.exceptions import (
    QuotientAIAuthException,
    QuotientAIException,
    QuotientAIInvalidInputException,
)
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from supabase import PostgrestAPIError, PostgrestAPIResponse, create_client


class FastAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Status code: {status_code}, Detail: {detail}")


class QuotientClient:
    def __init__(self):
        # Public API key for the QuotientAI Supabase project
        self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhocXBwY3FsdGtsemZwZ2dkb2NiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDEzNTU4MzgsImV4cCI6MjAxNjkzMTgzOH0.bpOtVl7co6B4wXQqt6Ec-WCz9FuO7tpVYbTa6PLoheI"

        # Base URL for the Supabase project
        self.supabase_url = "https://hhqppcqltklzfpggdocb.supabase.co"

        # Eval Scheduler config
        self.eval_scheduler_url = (
            "http://eval-scheduler-alb-887401167.us-east-2.elb.amazonaws.com"
        )
        self.supaclient = create_client(self.supabase_url, self.public_api_key)

        # Client Auth Token
        self.token = None
        self.token_expiry = 0
        self.api_key = os.environ.get("QUOTIENT_API_KEY")

        # Use API key if provided
        if self.api_key:
            self.supaclient._auth_token = {"Authorization": f"Bearer {self.api_key}"}

    def require_api_key(func):
        """Decorator to ensure an API key is present before calling the function."""

        def wrapper(self, *args, **kwargs):
            if not self.supaclient._auth_token.get("Authorization"):
                raise QuotientAIException("Invalid request: Missing API key")
            return func(self, *args, **kwargs)

        return wrapper

    def status(self):
        current_time = time.time()
        if current_time >= self.token_expiry:
            self.token = None
            self.token_expiry = 0
        return {
            "active_login": self.token is not None,
            "api_key": self.api_key is not None,
        }

    def login(self, email: str, password: str) -> str:
        login_data = {"email": email, "password": password}
        login_headers = {"apikey": self.public_api_key}
        try:
            response = requests.post(
                self.supabase_url + "/auth/v1/token?grant_type=password",
                json=login_data,
                headers=login_headers,
            )
            if 400 <= response.status_code < 500:
                raise ValueError(
                    f"Login failed with code {response.status_code}: {response.json()['error_description']}"
                )
            response.raise_for_status()  # Raises HTTPError for all non-4xx bad responses
            session = response.json()

            if "access_token" not in session or not session["access_token"]:
                raise ValueError("Login failed: No authentication token received")

            self.token = session["access_token"]
            self.token_expiry = (
                time.time() + session["expires_in"] - 60
            )  # Extra 60 seconds for buffer
            return "Login successful"

        except (ConnectionError, Timeout) as exc:
            raise QuotientAIException(
                "Login failed: Network error. Please check your connection and try again."
            ) from exc
        except HTTPError as http_err:
            raise QuotientAIException(
                f"Login failed: Server error {http_err.response.status_code}"
            ) from http_err
        except Exception as ve:
            raise QuotientAIException(str(ve)) from ve

    def sign_out(self) -> str:
        logout_headers = {
            "apikey": self.public_api_key,
            "Authorization": f"Bearer {self.token}",
        }
        try:
            response = requests.post(
                self.supabase_url + "/auth/v1/logout?scope=global",
                headers=logout_headers,
            )

            if response.status_code != 204:
                error_message = response.json().get(
                    "error_description", "Unknown error"
                )
                raise ValueError(
                    f"Sign out failed with code {response.status_code}: {error_message}"
                )

            # Clear the token and expiry
            self.token = None
            self.token_expiry = 0
            self.supaclient._auth_token = None

            # Return a message based on whether an API key is still in place
            if self.api_key:
                return "Sign out successful. API key still in place."
            return "Sign out successful."

        except (ConnectionError, Timeout) as exc:
            raise QuotientAIException(
                "Sign out failed: Network error. Please check your connection and try again."
            ) from exc
        except HTTPError as http_err:
            raise QuotientAIException(
                f"Sign out failed: Server error {http_err.response.status_code}"
            ) from http_err
        except Exception as e:
            raise QuotientAIException(f"Sign out failed: {str(e)}") from e

    ###########################
    #         API Keys        #
    ###########################

    def create_api_key(self, key_name: str, key_lifetime: int = 30) -> str:
        try:
            if not self.token:
                raise ValueError("Not logged in. Please log in first.")

            if self.api_key:
                raise ValueError("API key already exists. Please remove it first.")

            self.supaclient._auth_token = {"Authorization": f"Bearer {self.token}"}
            params = {"key_name": key_name, "key_lifetime": key_lifetime}
            response = self.supaclient.rpc("create_api_key", params=params).execute()

            if not response.data:
                raise ValueError("API key not returned. Unknown error.")

            self.api_key = response.data
            self.supaclient._auth_token = {"Authorization": f"Bearer {self.api_key}"}

            print(
                f"API keys are only returned once. Please store this key and its name in a secure location, and add it to your environment variables."
            )
            return response.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to create API key: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create API key: {str(e)}") from e

    def set_api_key(self, api_key: str):
        # TODO: Check if key is valid
        self.api_key = api_key
        return f"Workspace set with API key."

    def get_api_key(self):
        if not self.api_key:
            self.api_key = None
            return "No API key set"
        try:
            response = self.supaclient.table("api_keys").select("*").execute()
            # TODO: JWT tid filter
            return response.data[0]["key_name"]
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to get API key information: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to get API key information: {str(e)}"
            ) from e

    def remove_api_key(self):
        self.api_key = None
        if self.token and self.token_expiry > time.time():
            print("API key removed. You are still logged in.")
        else:
            print("API key removed")

    @require_api_key
    def list_api_keys(self):
        try:
            response = self.supaclient.table("api_keys").select("*").execute()
            if not response.data:
                raise ValueError("API keys not returned")
            return response.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list API keys: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list API keys: {str(e)}") from e

    @require_api_key
    def revoke_api_key(self, key_name: str):
        try:
            self.supaclient.table("api_keys").update({"revoked": True}).eq(
                "key_name", key_name
            ).execute()
            return f"API key {key_name} revoked successfully"
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to revoke API key: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to revoke API key: {str(e)}") from e

    ###########################
    #         Models          #
    ###########################

    @require_api_key
    def list_models(self, filters=None):
        try:
            query = self.supaclient.table("model").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list models: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list models: {str(e)}") from e

    ###########################
    #     System Prompts     #
    ###########################

    @require_api_key
    def list_system_prompts(self, filters=None):
        try:
            query = self.supaclient.table("system_prompt").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list system prompts: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list system prompts: {str(e)}") from e

    @require_api_key
    def create_system_prompt(self, message_string: str, name: str):
        try:
            params = {
                "name": name,
                "message_string": message_string,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.supaclient.table("system_prompt").insert(params).execute()

            if not response.data:
                raise ValueError("System prompt record not returned. Unknown error.")

            return response.data[0]
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to create system prompt: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to create system prompt: {str(e)}"
            ) from e

    @require_api_key
    def delete_system_prompt(self, system_prompt_id: int):
        try:
            response = (
                self.supaclient.table("system_prompt")
                .delete()
                .eq("id", system_prompt_id)
                .execute()
            )
            if not response.data:
                raise ValueError("system prompt not deleted (unknown error)")
            print(f"system prompt {response.data[0]['name']} deleted")
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to delete system prompt: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to delete system prompt: {str(e)}"
            ) from e

    ###########################
    #     Prompt Templates    #
    ###########################

    @require_api_key
    def list_prompt_templates(self, filters=None):
        try:
            query = self.supaclient.table("prompt_template").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list prompt templates: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to list prompt templates: {str(e)}"
            ) from e

    @require_api_key
    def create_prompt_template(self, template, name):
        try:
            url = f"{self.eval_scheduler_url}/create-prompt-template"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            params = {"template": template, "name": name}
            response = requests.post(url, headers=headers, params=params)
            result = response.json()
            if response.status_code != 200:
                if "detail" in result:
                    raise FastAPIError(response.status_code, result["detail"])
                else:
                    response.raise_for_status()
            return result
        except FastAPIError as fast_err:
            raise QuotientAIException(
                f"Failed to create prompt template: {fast_err.status_code} {fast_err.detail}"
            ) from fast_err
        except (ConnectionError, Timeout) as exc:
            raise QuotientAIException(
                "Failed to create prompt template: Network error. Please check your connection and try again."
            ) from exc
        except HTTPError as http_err:
            raise QuotientAIException(
                f"Failed to create prompt template: Server error {http_err.response.status_code}"
            ) from http_err
        except ValueError as ve:
            raise QuotientAIException(str(ve)) from ve

    @require_api_key
    def delete_prompt_template(self, template_id):
        try:
            response = (
                self.supaclient.table("prompt_template")
                .delete()
                .eq("id", template_id)
                .execute()
            )
            if not response.data:
                raise ValueError("Prompt template not deleted (unknown error)")
            print(f"Prompt template {response.data[0]['name']} deleted")
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to delete prompt template: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to delete prompt template: {str(e)}"
            ) from e

    ###########################
    #         Recipes         #
    ###########################

    @require_api_key
    def list_recipes(self, filters=None):
        try:
            query = self.supaclient.table("recipe").select(
                "*,prompt_template(*),model(*)"
            )
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list recipes: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list recipes: {str(e)}") from e

    @require_api_key
    def create_recipe(
        self,
        model_id: int,
        prompt_template_id: int,
        system_prompt_id: int | None = None,
        name: str = None,
        description: str = None,
    ):
        recipe = {"model_id": model_id, "prompt_template_id": prompt_template_id}
        recipe.update({"created_at": datetime.utcnow().isoformat()})
        if name:
            recipe.update({"name": name})
        if description:
            recipe.update({"description": description})
        if system_prompt_id:
            recipe.update({"system_prompt_id": system_prompt_id})
        try:
            response = self.supaclient.table("recipe").insert(recipe).execute()
            recipe_response = response.data[0]
            recipe_id = recipe_response["id"]
            # Supabase does not support returning nested objects, so we need to
            # manually fetch the prompt template and model after create
            return self.list_recipes({"id": recipe_id})[0]
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to create recipe: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create recipe: {str(e)}") from e

    @require_api_key
    def delete_recipe(self, recipe_id):
        try:
            response = (
                self.supaclient.table("recipe").delete().eq("id", recipe_id).execute()
            )
            if not response.data:
                raise ValueError("Recipe not deleted (unknown error)")
            print(f"Recipe {response.data[0]['name']} deleted")
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to delete recipe: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to delete recipe: {str(e)}") from e

    ###########################
    #         Datasets        #
    ###########################

    @require_api_key
    def list_datasets(self, filters=None):
        try:
            query = self.supaclient.table("dataset").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list datasets: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list datasets: {str(e)}") from e

    @require_api_key
    def create_dataset(self, file_path: str, name: str):
        try:
            url = f"{self.eval_scheduler_url}/upload-dataset"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }

            # Client-side file size check
            size_threshold = 2 * 1024**3  # 2GB
            file_size = os.path.getsize(file_path)
            if file_size > size_threshold:
                raise QuotientAIInvalidInputException("File size exceeds 2GB limit")

            # Guess the MIME type of the file
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                raise QuotientAIException(
                    "Could not determine the file's MIME type. Make sure your file is a `.csv` and try again"
                )

            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as file:
                files = {"file": (file_name, file, mime_type)}
                response = requests.post(
                    url, headers=headers, params={"name": name}, files=files
                )
                response.raise_for_status()
                dataset_id = response.json()["id"]
                return self.list_datasets({"id": dataset_id})[0]
        except QuotientAIInvalidInputException as e:
            raise QuotientAIException(f"Failed to create dataset: {str(e)}") from e
        except RequestException as e:
            raise QuotientAIException(
                f"Failed to upload dataset: {e.response.text}"
            ) from e
        except Exception as e:
            raise QuotientAIException(f"Failed to create dataset: {str(e)}") from e

    ###########################
    #          Tasks          #
    ###########################

    @require_api_key
    def list_tasks(self, filters=None):
        try:
            query = self.supaclient.table("task").select("*,dataset(*)")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list tasks: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list tasks: {str(e)}") from e

    @require_api_key
    def create_task(self, dataset_id, name, task_type):
        try:
            task_data = {
                "dataset_id": dataset_id,
                "name": name,
                "task_type": task_type,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.supaclient.table("task").insert(task_data).execute()
            if not response.data:
                raise ValueError("Task creation failed, no data returned.")
            task_id = response.data[0]["id"]
            # Supabase does not support returning nested objects, so we need to
            # manually fetch the dataset after create
            return self.list_tasks({"id": task_id})[0]

        except ValueError as e:
            raise QuotientAIException(f"Failed to create task: {e}") from e
        except Exception as e:
            # Catch-all for unexpected errors
            raise QuotientAIException(
                f"An unexpected error occurred during task creation: {str(e)}"
            ) from e

    ###########################
    #          Jobs           #
    ###########################

    @require_api_key
    def list_jobs(self, filters=None):
        try:
            query = self.supaclient.table("job").select("*,task(*),recipe(*)")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except PostgrestAPIError as api_err:
            raise QuotientAIException(
                f"Failed to list jobs: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list jobs: {str(e)}") from e

    @require_api_key
    def create_job(
        self, task_id, recipe_id, num_fewshot_examples=0, limit=100, seed=42
    ):
        job_data = {
            "task_id": task_id,
            "recipe_id": recipe_id,
            "num_fewshot_examples": num_fewshot_examples,
            "limit": limit,
            "seed": seed,
        }
        try:
            url = f"{self.eval_scheduler_url}/create-eval-job"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            response = requests.post(url, headers=headers, params=job_data)
            result = response.json()
            if response.status_code != 200:
                if "detail" in result:
                    raise FastAPIError(response.status_code, result["detail"])
                else:
                    response.raise_for_status()
            job_id = result["id"]
            # Supabase does not support returning nested objects, so we need to
            # manually fetch the task after create
            return self.list_jobs({"id": job_id})[0]
        except FastAPIError as fast_err:
            raise QuotientAIException(
                f"Failed to create job: {fast_err.status_code} {fast_err.detail}"
            ) from fast_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create job: {str(e)}") from e

    @require_api_key
    def get_eval_results(self, job_id):
        try:
            url = f"{self.eval_scheduler_url}/get-eval-results"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            response = requests.get(url, headers=headers, params={"job_id": job_id})
            response.raise_for_status()
            results = response.json()
            return results
        except (ConnectionError, Timeout) as exc:
            raise QuotientAIException(
                "Failed to get eval results: Network error. Please check your connection and try again."
            ) from exc
        except HTTPError as http_err:
            raise QuotientAIException(
                f"Failed to get eval results: Server error {http_err.response.status_code}"
            ) from http_err
        except ValueError as ve:
            raise QuotientAIException(str(ve)) from ve
