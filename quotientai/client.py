import json
import mimetypes
import os
import time
from datetime import datetime
from typing import List

import requests
from postgrest import APIError, SyncPostgrestClient
from quotientai._enums import GenerateDatasetType
from quotientai.exceptions import QuotientAIException, QuotientAIInvalidInputException
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout


class FastAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Status code: {status_code}, Detail: {detail}")


class QuotientClient:
    """
    A client that provides access to the QuotientAI API.

    The QuotientClient class provides methods to interact with the QuotientAI API, including
    logging in, creating and managing API keys, and creating and managing models, system prompts,
    prompt templates, recipes, datasets, and tasks.
    """

    def __init__(self):
        # Public API key for the QuotientAI Supabase project
        self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhocXBwY3FsdGtsemZwZ2dkb2NiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDEzNTU4MzgsImV4cCI6MjAxNjkzMTgzOH0.bpOtVl7co6B4wXQqt6Ec-WCz9FuO7tpVYbTa6PLoheI"

        # Base URL for the Supabase project
        self.supabase_url = "https://hhqppcqltklzfpggdocb.supabase.co"

        self.eval_scheduler_url = "http://eval-scheduler-alb-887401167.us-east-2.elb.amazonaws.com"

        self.supaclient = SyncPostgrestClient(
            self.supabase_url + "/rest/v1", headers={"apiKey": self.public_api_key}
        )

        # Client Auth Token
        self.token = None
        self.token_expiry = 0
        self.api_key = os.environ.get("QUOTIENT_API_KEY")

        # Use API key if provided
        if self.api_key:
            self.supaclient.auth(self.api_key)

    def require_api_key(func):
        """Decorator to ensure an API key is present before calling the function."""

        def wrapper(self, *args, **kwargs):
            if not self.api_key:
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
        login_headers = {"apiKey": self.public_api_key}
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
            self.supaclient.auth(self.token)
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
            "apiKey": self.public_api_key,
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

            # Return a message based on whether an API key is still in place
            if self.api_key:
                self.supaclient.auth(self.api_key)
                return "Sign out successful. API key still in place."
            self.supaclient.auth(self.public_api_key)
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

    def end_session(self) -> str:
        self.token = None
        self.token_expiry = 0
        self.supaclient.aclose()
        return "Session ended"

    ###########################
    #         API Keys        #
    ###########################

    def create_api_key(self, key_name: str, key_lifetime: int = 30) -> str:
        """
        Create a new API key with a given name and lifetime.

        Parameters:
        -----------
        key_name : str
            The name of the API key
        key_lifetime : int, optional
            The lifetime of the API key in days. Default is 30 days.

        Returns:
        --------
        str
            The value of the API key
        """
        try:
            if not self.token:
                raise ValueError("Not logged in. Please log in first.")

            if self.api_key:
                raise ValueError("API key already exists. Please remove it first.")

            params = {"key_name": key_name, "key_lifetime": key_lifetime}
            rpc_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "apiKey": self.public_api_key,
                "Authorization": f"Bearer {self.token}",
            }

            response = requests.post(
                self.supabase_url + "/rest/v1/rpc/create_api_key",
                json=params,
                headers=rpc_headers,
            )
            if response.status_code == 400:
                raise ValueError(
                    f"Code {response.status_code}: {response.json()['message']}"
                )
            response.raise_for_status()
            result = response.json()
            if not result:
                raise ValueError("API key not returned. Unknown error.")
            self.api_key = result
            self.supaclient.auth(result)

            print(
                "API keys are only returned once. Please store this key and its name in a secure location, and add it to your environment variables."
            )
            return result
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to create API key: {api_err.message} ({api_err.code})"
            ) from api_err
        except HTTPError as http_err:
            raise QuotientAIException(
                f"Failed to create API key: ({http_err.response.status_code}) - {http_err.response.text}"
            ) from http_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create API key: {str(e)}") from e

    def set_api_key(self, api_key: str):
        # TODO: Check if key is valid
        self.api_key = api_key
        return "Workspace set with API key."

    def get_api_key(self):
        if not self.api_key:
            self.api_key = None
            return "No API key set"
        try:
            response = self.supaclient.from_("api_keys").select("*").execute()
            # TODO: JWT tid filter
            return response.data[0]["key_name"]
        except APIError as api_err:
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
            self.supaclient.auth(self.token)
            print("API key removed. You are still logged in.")
        else:
            self.supaclient.auth(self.public_api_key)
            print("API key removed.")

    @require_api_key
    def list_api_keys(self):
        try:
            response = self.supaclient.from_("api_keys").select("*").execute()
            if not response.data:
                raise ValueError("API keys not returned")
            return response.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list API keys: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list API keys: {str(e)}") from e

    @require_api_key
    def revoke_api_key(self, key_name: str):
        try:
            self.supaclient.from_("api_keys").update({"revoked": True}).eq(
                "key_name", key_name
            ).execute()
            return f"API key {key_name} revoked successfully"
        except APIError as api_err:
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
            query = self.supaclient.from_("model").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list models: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list models: {str(e)}") from e

    @require_api_key
    def create_model(
        self,
        name: str,
        endpoint: str,
        description: str,
        method: str,
        headers: dict,
        payload_template: dict,
        path_to_data: str,
        path_to_context: str,
        model_type: str = "UserHostedModel",
    ) -> dict:
        external_model_config = {
            "method": method,
            "headers": json.dumps(headers),
            "payload_template": json.dumps(payload_template),
            "path_to_data": path_to_data,
            "path_to_context": path_to_context,
            "created_at": datetime.utcnow().isoformat(),
        }

        model = {
            "name": name,
            "endpoint": endpoint,
            "revision": "placeholder",
            "model_type": model_type,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "instruction_template_cls": "NoneType",
        }

        try:
            response = (
                self.supaclient.from_("external_model_config")
                .insert(external_model_config)
                .execute()
            )
            model_config_response = response.data[0]
            model_config_id = model_config_response["id"]

            model.update({"external_model_config_id": model_config_id})
            response = self.supaclient.from_("model").insert(model).execute()
            model_response = response.data[0]
            return model_response

        except APIError as api_err:
            print("exception", api_err)
            raise QuotientAIException(
                f"Failed to create model: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create model: {str(e)}") from e

    @require_api_key
    def delete_model(self, model_id: int):
        try:
            # pull the model and see if the model as any external model config
            model = (
                self.supaclient.from_("model").select("*").eq("id", model_id).execute()
            )
            if not model.data:
                raise ValueError("Model not found")

            model_data = model.data[0]
            external_model_config_id = model_data.get("external_model_config_id")

            response = (
                self.supaclient.from_("model").delete().eq("id", model_id).execute()
            )

            if external_model_config_id:
                # delete the external model config
                self.supaclient.from_("external_model_config").delete().eq(
                    "id", external_model_config_id
                ).execute()

            if not response.data:
                raise ValueError("Model not deleted (unknown error)")
            print(f"Model {response.data[0]['name']} deleted")
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to delete model: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to delete model: {str(e)}") from e

    ###########################
    #     System Prompts     #
    ###########################

    @require_api_key
    def list_system_prompts(self, filters=None):
        try:
            query = self.supaclient.from_("system_prompt").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list system prompts: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list system prompts: {str(e)}") from e

    @require_api_key
    def create_system_prompt(self, message_string: str, name: str) -> dict:
        """
        Create a new system prompt with a given message string and name.

        Parameters:
        -----------
        message_string : str
            The message string to use for the system prompt
        name : str
            The name of the system prompt

        Returns:
        --------
        dict
            The system prompt record from the API.
        """
        try:
            params = {
                "name": name,
                "message_string": message_string,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.supaclient.from_("system_prompt").insert(params).execute()

            if not response.data:
                raise ValueError("System prompt record not returned. Unknown error.")

            return response.data[0]
        except APIError as api_err:
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
            print(f"Deleting system prompt {system_prompt_id}")
            response = (
                self.supaclient.from_("system_prompt")
                .delete()
                .eq("id", system_prompt_id)
                .execute()
            )
            if not response.data:
                raise ValueError("system prompt not deleted (unknown error)")
        except APIError as api_err:
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
    def list_prompt_templates(self, filters=None) -> list:
        """
        List prompt templates with optional filters. If no filters are provided, all prompt templates are returned.

        Parameters:
        -----------
        filters : dict, optional
            A dictionary of equality filters to apply to the prompt template list. Default is None.
            Options are "id", "name", "created_at".

        Returns:
        --------
        list : A list of prompt template records from the API.
        """
        try:
            query = self.supaclient.from_("prompt_template").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list prompt templates: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to list prompt templates: {str(e)}"
            ) from e

    @require_api_key
    def create_prompt_template(self, template, name) -> dict:
        """
        Create a new prompt template with a given template and name.

        Parameters:
        -----------
        template : str
            The template string to use for the prompt template
        name : str
            The name of the prompt template

        Returns:
        --------
        dict
            The prompt template record from the API.
        """
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
                self.supaclient.from_("prompt_template")
                .delete()
                .eq("id", template_id)
                .execute()
            )
            if not response.data:
                raise ValueError("Prompt template not deleted (unknown error)")
        except APIError as api_err:
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
    def list_recipes(self, filters=None) -> list:
        """
        List recipes with optional filters. If no filters are provided, all recipes are returned.

        Parameters:
        -----------
        filters : dict, optional
            A dictionary of equality filters to apply to the recipe list. Default is None.
            Options are "id", "name", "model_id", "prompt_template_id", "created_at".

        Returns:
        --------
        list
            A list of recipe records from the API.
        """
        try:
            query = self.supaclient.from_("recipe").select(
                "*,prompt_template(*),model(*)"
            )
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
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
    ) -> dict:
        """
        Create a new recipe with a given model, prompt template, and optional system prompt.

        Parameters:
        -----------
        model_id : int
            The ID of the model to use for the recipe
        prompt_template_id : int
            The ID of the prompt template to use for the recipe
        system_prompt_id : int, optional
            The ID of the system prompt to use for the recipe. Default is None.
        name : str, optional
            The name of the recipe. Default is None.
        description : str, optional
            The description of the recipe. Default is None.

        Returns:
        --------
        dict
            The recipe record from the API.
        """
        recipe = {"model_id": model_id, "prompt_template_id": prompt_template_id}
        recipe.update({"created_at": datetime.utcnow().isoformat()})
        if name:
            recipe.update({"name": name})
        if description:
            recipe.update({"description": description})
        if system_prompt_id:
            recipe.update({"system_prompt_id": system_prompt_id})
        try:
            response = self.supaclient.from_("recipe").insert(recipe).execute()
            recipe_response = response.data[0]
            recipe_id = recipe_response["id"]
            # Supabase does not support returning nested objects, so we need to
            # manually fetch the prompt template and model after create
            return self.list_recipes({"id": recipe_id})[0]
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to create recipe: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create recipe: {str(e)}") from e

    @require_api_key
    def delete_recipe(self, recipe_id):
        try:
            response = (
                self.supaclient.from_("recipe").delete().eq("id", recipe_id).execute()
            )
            if not response.data:
                raise ValueError("Recipe not deleted (unknown error)")
            print(f"Recipe {response.data[0]['name']} deleted")
        except APIError as api_err:
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
        """
        List datasets with optional filters. If no filters are provided, all datasets are returned.

        Parameters:
        -----------
        filters : dict, optional
            A dictionary of equality filters to apply to the dataset list. Default is None.
            Options are "id", "name", "created_at".

        Returns:
        --------
        list
            A list of dataset records from the API.
        """
        try:
            query = self.supaclient.from_("dataset").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list datasets: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list datasets: {str(e)}") from e

    @require_api_key
    def create_dataset(self, file_path: str, name: str) -> dict:
        """
        Create a new dataset with a given file and name.

        Parameters:
        -----------
        file_path : str
            The path to the file to upload.
        name : str
            The name of the dataset once uploaded to Quotient.

        Returns:
        --------
        dict
            The dataset record from the API.
        """
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
    def list_tasks(self, filters=None) -> list:
        """
        List tasks with optional filters. If no filters are provided, all tasks are returned.

        Parameters:
        -----------
        filters : dict, optional
            A dictionary of equality filters to apply to the task list. Default is None.
            Options are "id", "name", "task_type", "dataset_id", "created_at".
        """
        try:
            query = self.supaclient.from_("task").select("*,dataset(*)")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list tasks: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list tasks: {str(e)}") from e

    @require_api_key
    def create_task(self, dataset_id, name, task_type) -> dict:
        """
        Create a new task with a given dataset, name, and task type.

        Parameters:
        -----------
        dataset_id : int
            The ID of the dataset to use for the task
        name : str
            The name of the task
        task_type : str
            The type of task to create. Must be one of "question_answering" or "summarization"

        Returns:
        --------
        dict
            The task record from the API.
        """
        if task_type not in ["question_answering", "summarization"]:
            raise QuotientAIInvalidInputException(
                "Task type must be one of 'question_answering' or 'summarization'"
            )

        try:
            task_data = {
                "dataset_id": dataset_id,
                "name": name,
                "task_type": task_type,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.supaclient.from_("task").insert(task_data).execute()
            if not response.data:
                raise ValueError("Task creation failed, no data returned.")
            task_id = response.data[0]["id"]
            # Supabase does not support returning nested objects, so we need to
            # manually fetch the dataset after create
            return self.list_tasks({"id": task_id})[0]

        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to create task: {api_err.message} ({api_err.code})"
            ) from api_err
        except ValueError as e:
            raise QuotientAIException(f"Failed to create task: {e}") from e
        except Exception as e:
            # Catch-all for unexpected errors
            raise QuotientAIException(
                f"An unexpected error occurred during task creation: {str(e)}"
            ) from e

    @require_api_key
    def delete_task(self, task_id):
        try:
            response = (
                self.supaclient.from_("task").delete().eq("id", task_id).execute()
            )
            if not response.data:
                raise ValueError("task not deleted (unknown error)")
            print(f"task {response.data[0]['name']} deleted")
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to delete task: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to delete task: {str(e)}") from e

    ###########################
    #          Jobs           #
    ###########################

    @require_api_key
    def list_jobs(self, filters=None) -> list:
        """
        List jobs with optional filters. If no filters are provided, all jobs are returned.

        Parameters:
        -----------
        filters : dict, optional
            A dictionary of equality filters to apply to the job list. Default is None.
            Options are "id", "task_id", "recipe_id", "status", "created_at".

        Returns:
        --------
        list
            A list of job records from the API.
        """
        try:
            query = self.supaclient.from_("job").select("*,task(*),recipe(*)")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            data = query.execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to list jobs: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to list jobs: {str(e)}") from e

    @require_api_key
    def create_job(
        self,
        task_id,
        recipe_id,
        num_fewshot_examples=0,
        limit=100,
        seed=42,
        metric_ids=None,
    ):
        """
        Create a new job with a given task, recipe, and optional parameters.

        Parameters:
        ----------
        task_id : int
            The ID of the task to evaluate
        recipe_id : int
            The ID of the recipe to use for evaluation
        num_fewshot_examples : int, optional
            The number of few-shot examples to use for evaluation. Default is 0.
        limit : int, optional
            The number of examples to evaluate. Default is 100.
        seed : int, optional
            The random seed to use for evaluation. Default is 42.
        metric_ids : list[int], optional
            A list of metrics to use for evaluation. Default is None.

        Returns:
        --------
        dict
            The job record from the API.
        """
        job_data = {
            "task_id": task_id,
            "recipe_id": recipe_id,
            "num_fewshot_examples": num_fewshot_examples,
            "limit": limit,
            "seed": seed,
        }

        if metric_ids is not None:
            job_data.update({"metric_ids": metric_ids})

        try:
            url = f"{self.eval_scheduler_url}/create-eval-job"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            response = requests.post(url, headers=headers, json=job_data)
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
    def get_eval_results(self, job_id: int) -> dict:
        """
        Get the results of an evaluation job.

        Parameters:
        -----------
        job_id : int
            The ID of the job to get results for.

        Returns:
        --------
        dict : The results of the evaluation job.
        """
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

    @require_api_key
    def delete_job(self, job_id):
        try:
            # Before we can delete a job, we also need to find all the progress records associated with the job and delete them.
            progress_records = (
                self.supaclient.from_("job_progress")
                .select("id")
                .eq("job_id", job_id)
                .execute()
            )
            if progress_records.data:
                for progress_record in progress_records.data:
                    self.supaclient.from_("job_progress").delete().eq(
                        "id", progress_record["id"]
                    ).execute()

            response = self.supaclient.from_("job").delete().eq("id", job_id).execute()
            if not response.data:
                raise ValueError("Job not deleted (unknown error)")
            print(f"Job {response.data[0]['id']} deleted")
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to delete job: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to delete job: {str(e)}") from e

    ###########################
    #          Progress       #
    ###########################

    @require_api_key
    def list_job_progress(self, job_id):
        try:
            data = (
                self.supaclient.from_("job_progress")
                .select("*")
                .eq("job_id", job_id)
                .execute()
            )
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to retrieve job progress: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to retrieve job progress: {str(e)}"
            ) from e

    ###########################
    #          Metrics        #
    ###########################

    @require_api_key
    def create_rubric_based_metric(
        self, name: str, description: str, model_id: int, rubric_template: str
    ) -> dict:
        """
        Create a new metric with a given name and description.

        Parameters:
        -----------
        name : str
            The name of the metric
        description : str
            The description of the metric
        model_id : int
            The ID of the model to use for the metric
        rubric_template : str
            The rubric template to use for the metric. Must include `{input_text}` with in the template.

        Returns:
        --------
        dict
            The metric record from the API.
        """
        try:
            # check for valid template
            if "{input_text}" not in rubric_template:
                raise QuotientAIException("Rubric template must include `{input_text}`")

            byo_metric_data = {
                "name": name,
                "rubric_template": rubric_template,
                "model_id": model_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = (
                self.supaclient.from_("byo_rubric_metric")
                .insert(byo_metric_data)
                .execute()
            )
            byo_rubric_metric_id = response.data[0]["id"]

            metric_data = {
                "name": name,
                "title": name,
                "description": description,
                "byo_rubric_metric_id": byo_rubric_metric_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.supaclient.from_("metrics").insert(metric_data).execute()
            if not response.data:
                raise ValueError("Metric creation failed, no data returned.")
            return response.data[0]
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to create metric: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(f"Failed to create metric: {str(e)}") from e

    @require_api_key
    def list_metrics(self):
        try:
            data = self.supaclient.from_("metrics").select("*").execute()
            return data.data
        except APIError as api_err:
            raise QuotientAIException(
                f"Failed to retrieve job progress: {api_err.message} ({api_err.code})"
            ) from api_err
        except Exception as e:
            raise QuotientAIException(
                f"Failed to retrieve job progress: {str(e)}"
            ) from e

    @require_api_key
    def generate_examples(
        self,
        generation_type: GenerateDatasetType,
        description: str,
        num_examples: int = 3,
        seed_data: str = None,
        preferences: List[dict] = None,
    ) -> List[str]:
        try:
            url = f"{self.eval_scheduler_url}/generate/examples"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            params = {
                "generation_type": generation_type.value,
            }

            data = {
                "inputs": seed_data,
                "description": description,
                "num_examples": num_examples,
                "preferences": preferences,
            }
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
            )
            result = response.json()
            if response.status_code != 200:
                if "detail" in result:
                    raise FastAPIError(response.status_code, result["detail"])
                else:
                    response.raise_for_status()

            return result
        except FastAPIError as fast_err:
            raise QuotientAIException(
                f"Failed to generate examples: {fast_err.status_code} {fast_err.detail}"
            ) from fast_err

        except Exception as e:
            raise QuotientAIException(f"Failed to generate examples: {str(e)}") from e

    @require_api_key
    def generate_dataset(
        self,
        generation_type: GenerateDatasetType,
        description: str,
        num_examples: int = 3,
        seed_data: str = None,
        preferences: List[dict] = None,
    ) -> List[str]:
        try:
            url = f"{self.eval_scheduler_url}/generate/dataset"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            params = {
                "generation_type": generation_type.value,
            }

            data = {
                "inputs": seed_data,
                "description": description,
                "num_examples": num_examples,
                "preferences": preferences,
            }
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=data,
            )
            result = response.json()
            if response.status_code != 200:
                if "detail" in result:
                    raise FastAPIError(response.status_code, result["detail"])
                else:
                    response.raise_for_status()

            return result
        except FastAPIError as fast_err:
            raise QuotientAIException(
                f"Failed to generate dataset: {fast_err.status_code} {fast_err.detail}"
            ) from fast_err

        except Exception as e:
            raise QuotientAIException(f"Failed to generate dataset: {str(e)}") from e
