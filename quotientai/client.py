import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.WARNING)

from supabase import create_client
import requests


class QuotientClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

        # Public API key for the QuotientAI Supabase project
        self.public_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhocXBwY3FsdGtsemZwZ2dkb2NiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDEzNTU4MzgsImV4cCI6MjAxNjkzMTgzOH0.bpOtVl7co6B4wXQqt6Ec-WCz9FuO7tpVYbTa6PLoheI"
        self.supabase_url = "https://hhqppcqltklzfpggdocb.supabase.co"
        self.supabase_client = create_client(self.supabase_url, self.public_api_key)

        # Eval Scheduler config
        self.eval_scheduler_url = "http://eval-scheduler-alb-887401167.us-east-2.elb.amazonaws.com"

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

        if response and hasattr(response, 'user'):
            print(f"Success! {self.email} has been registered!")

            if response.user.confirmed_at is None:
                print("Please check your inbox and verify your email before continuing.")

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

    def list_models(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("model").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def list_prompt_templates(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("prompt_template").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

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

    def list_datasets(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("dataset").select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def list_tasks(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("task").select("*,dataset(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def list_jobs(self, filters=None):
        self.check_token()
        query = self.supabase_client.table("job").select("*,task(*),recipe(*)")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        data = query.execute()
        return data.data

    def create_job(self, job):
        self.check_token()
        job.update({"status": "Scheduled"})
        job.update({"created_at": datetime.utcnow().isoformat()})
        query = self.supabase_client.table("job").insert(job)
        response = query.execute()
        job = response.data[0]
        job_id = job["id"]
        # Supabase does not support returning nested objects, so we need to
        # manually fetch the task and recipe after create
        return self.list_jobs({"id": job_id})[0]


    def get_eval_results(self, job_id):
        self.check_token()

        endpoint = 'get-eval-results'
        url = f'{self.eval_scheduler_url}/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers, params={'job_id': job_id})

        if response.status_code == 200:
            return response.json()
        else:
            return f"Failed with status code: {response.status_code}"
