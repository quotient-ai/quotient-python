import ast
import json
import logging
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
    def __init__(self, api_key=None):

        # Public API key for the QuotientAI Supabase project
        self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhocXBwY3FsdGtsemZwZ2dkb2NiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDEzNTU4MzgsImV4cCI6MjAxNjkzMTgzOH0.bpOtVl7co6B4wXQqt6Ec-WCz9FuO7tpVYbTa6PLoheI"
        self.supabase_url = "https://hhqppcqltklzfpggdocb.supabase.co"
        # Eval Scheduler config
        self.eval_scheduler_url = (
            "http://eval-scheduler-alb-887401167.us-east-2.elb.amazonaws.com"
        )

        # Local dev settings
        # self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
        # self.supabase_url = "http://127.0.0.1:54321"
        # self.eval_scheduler_url = "http://127.0.0.1:8000"

        # Client Auth Token
        self.token = None
        self.token_expiry = 0
        self.api_key = api_key

    # def register_user(self):
    #     response = self.supabase_client.auth.sign_up(
    #         {
    #             "email": self.email,
    #             "password": self.password,
    #         }
    #     )

    #     if response and hasattr(response, "user"):
    #         print(f"Success! {self.email} has been registered!")

    #         if response.user.confirmed_at is None:
    #             print(
    #                 "Please check your inbox and verify your email before continuing."
    #             )

    #     return response
        
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
        response = requests.post(self.supabase_url + "/auth/v1/token?grant_type=password", json=login_data, headers=login_headers)
        if response.status_code != 200:
            self.token = None
            self.token_expiry = 0
            raise ValueError(f"Login failed: Status code: {response.status_code}")
        session = response.json()
        if 'access_token' not in session or not session['access_token']:
            raise ValueError("Login failed: No authentication token received")
        self.token = session['access_token']
        self.token_expiry = time.time() + session['expires_in'] - 60  # Extra 60 seconds for buffer
        return "Login successful: Please create an API key to use the platform."

    def sign_out(self) -> str:
        logout_headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.supabase_url + "/auth/v1/logout?scope=global", headers=logout_headers)
        if response.status_code != 204:
            raise ValueError(f"Logout failed: Status code: {response.status_code}")
        self.token = None
        self.token_expiry = 0
        if self.api_key:
            return f"Sign out successful. API key still in place."
        return f"Sign out successful."

    # def check_token(self):
    #     current_time = time.time()
    #     if not self.token or current_time >= self.token_expiry:
    #         self.login_to_supabase()

    ###########################
    #         API Keys        #
    ###########################
    
    def create_api_key(self, key_name: str, key_lifetime: int = 30):
        supaclient = create_client(self.supabase_url, self.token)
        response = supaclient.rpc("create_api_key", {"key_name": key_name, "key_lifetime": key_lifetime}).execute()
        if not response.data:
            raise ValueError("API key not returned")
        self.api_key = response.data
        print(f"API keys are only returned once. Please store this key and its name in a secure location.")
        return response.data
    
    def set_api_key(self, api_key: str):
        # TODO: Check if key is valid
        self.api_key = api_key
        return f"Workspace set with API key."
    
    def get_api_key(self):
        if not self.api_key:
            self.api_key = None
            return "No API key set"
        supaclient = create_client(self.supabase_url, self.api_key)
        response = supaclient.table('api_keys').select("*").execute()
        # TODO: JWT tid filter
        return response.data[0]['key_name']
    
    def remove_api_key(self):
        self.api_key = None
        if self.token and self.token_expiry > time.time():
            return "API key removed. You are still logged in."
        return "API key removed"
    
    def list_api_keys(self):
        supaclient = create_client(self.supabase_url, self.api_key)
        response = supaclient.table('api_keys').select("*").execute()
        if not response.data:
            raise ValueError("API keys not returned")
        return response.data
    
    def revoke_api_key(self, key_name: str):
        supaclient = create_client(self.supabase_url, self.api_key)
        supaclient.table('api_keys').update({ "revoked": True }).eq('key_name', key_name).execute()
        self.api_key = None
        return f"API key {key_name} revoked successfully"

    ###########################
    #         Models          #
    ###########################

    def list_models(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("model").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    ###########################
    #     Prompt Templates    #
    ###########################

    def list_prompt_templates(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("prompt_template").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_prompt_template(self, template, name):
        url = f"{self.eval_scheduler_url}/create-prompt-template"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        params = {"template": template, "name": name}
        response = requests.post(url, headers=headers, params=params)
        status_code = response.status_code        
        if status_code == 500:
            raise QuotientAIInvalidInputException({
                "message": f"Failed to create prompt template: Eval scheduler not available (500).",
                "status_code": 500
            })
        result = response.json()
        if status_code != 200:
            raise QuotientAIInvalidInputException({
                "message": f"Failed to create prompt template: {result['detail']}",
                "status_code": status_code
            })
        return result

    def delete_prompt_template(self, template_id):
        supaclient = create_client(self.supabase_url, self.api_key)
        response = supaclient.table("prompt_template").delete().eq("id", template_id).execute()
        if not response.data:
            raise QuotientAIAuthException(
                f"Failed to delete prompt template with id {template_id}. Does not exist or unauthorized."
            )
        return f"Prompt template {response.data[0]['name']} deleted"

    ###########################
    #         Recipes         #
    ###########################

    def list_recipes(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("recipe").select(
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
        supaclient = create_client(self.supabase_url, self.api_key)
        recipe = {"model_id": model_id, "prompt_template_id": prompt_template_id}
        recipe.update({"created_at": datetime.utcnow().isoformat()})
        if name:
            recipe.update({"name": name})
        if description:
            recipe.update({"description": description})
        query = supaclient.table("recipe").insert(recipe)
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
    
    def delete_recipe(self, recipe_id):
        supaclient = create_client(self.supabase_url, self.api_key)
        response = supaclient.table("recipe").delete().eq("id", recipe_id).execute()
        if not response.data:
            raise QuotientAIAuthException(
                f"Failed to delete recipe with id {recipe_id}. Does not exist or unauthorized."
            )
        return f"Recipe {response.data[0]['name']} deleted"

    ###########################
    #         Datasets        #
    ###########################

    def list_datasets(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("dataset").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    ###########################
    #          Tasks          #
    ###########################

    def list_tasks(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("task").select("*,dataset(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    ###########################
    #          Jobs           #
    ###########################

    def list_jobs(self, filters=None):
        supaclient = create_client(self.supabase_url, self.api_key)
        query = supaclient.table("job").select("*,task(*),recipe(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_job(self, task_id, recipe_id, num_fewshot_examples, limit):
        supaclient = create_client(self.supabase_url, self.api_key)
        job_data = {"task_id": task_id, "recipe_id": recipe_id, "num_fewshot_examples": num_fewshot_examples, "limit": limit}
        job_data.update({"status": "Scheduled"})
        job_data.update({"created_at": datetime.utcnow().isoformat()})
        response = supaclient.table("job").insert(job_data).execute()
        job = response.data[0]
        job_id = job["id"]
        # Supabase does not support returning nested objects, so we need to
        # manually fetch the task and recipe after create
        return self.list_jobs({"id": job_id})[0]

    def get_eval_results(self, job_id):
        url = f"{self.eval_scheduler_url}/get-eval-results"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers, params={"job_id": job_id})
        status_code = response.status_code        
        if status_code == 500:
            raise QuotientAIInvalidInputException({
                "message": "Failed to get results: Results endpoint not available.",
                "status_code": status_code
            })
        results = response.json()
        if status_code != 200:
            detail = results.get('detail', "Failed to get results: No detail provided")
            raise QuotientAIInvalidInputException({
                "message": f"Failed to get results: {detail}",
                "status_code": status_code
            })
        if not results:
            raise QuotientAIAuthException(
                f"Failed to get eval results for job {job_id}."
            )
        return results[0]
