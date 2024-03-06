import pytest
import os
import time
from supabase import create_client
from quotientai import QuotientClient 

from quotientai.exceptions import QuotientAIException

if 'QUOTIENT_API_KEY' in os.environ:
    del os.environ['QUOTIENT_API_KEY']

from .constants import (
    TEST_USER_EMAIL, 
    TEST_INVALID_PASSWORD, 
    TEST_USER_PASSWORD, 
    TEST_API_KEY_NAME, 
    TEST_CREATE_SYSTEM_PROMPT,
    TEST_BAD_PROMPT_TEMPLATE,
    TEST_CREATE_PROMPT_TEMPLATE, 
    TEST_USER_ID, 
    SUPABASE_URL, 
    SUPABASE_ADMIN_KEY
)

client = QuotientClient()


###########################
#      Setup/Cleanup      #
###########################

@pytest.fixture(scope="module")
def test_ids():
    keys = {
        'test_template_id': None,
        'test_prompt_id': None,
        'test_recipe_id': None,
        'test_job_id': None
    }
    yield keys

@pytest.fixture(scope="module", autouse=True)
def teardown_module():
    """Cleanup function to run after all tests in this module."""
    # Setup code
    if 'QUOTIENT_API_KEY' in os.environ:
        del os.environ['QUOTIENT_API_KEY']
    yield
     # Teardown code
    client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
    response = client.table('profile').select('id').eq('uid', TEST_USER_ID).execute()
    if not response.data:
        print("No profile found for test user: Cleanup not done")
        return
    profile_id = response.data[0]['id']
    client.table('api_keys').delete().eq('user_id', TEST_USER_ID).execute()
    client.table('job').delete().eq('owner_profile_id', profile_id).execute()
    print("SDK tests cleanup completed")

###########################
#      Without creds      #
###########################

def test_invalid_credentials():
    with pytest.raises(QuotientAIException) as exc_info:
        client.login(TEST_USER_EMAIL, TEST_INVALID_PASSWORD)
    assert "Invalid login credentials" in str(exc_info.value), "Expected invalid credentials to raise an exception"

def test_missing_credentials():
    with pytest.raises(QuotientAIException) as exc_info:
        client.create_api_key(TEST_API_KEY_NAME, 30)
    assert "Not logged in" in str(exc_info.value), "Expected missing credentials to raise an exception"


###########################
#       Create creds      #
###########################
        
def test_successful_login():
    result = client.login(TEST_USER_EMAIL, TEST_USER_PASSWORD)
    assert "Login successful" in result, "Expected login to be successful"
    assert client.token is not None, "Expected token to be set after login"

def test_api_key_failure():
    with pytest.raises(QuotientAIException) as exc_info:
        client.create_api_key("badname", 60)
    assert "Invalid key name length" in str(exc_info.value), "Expected key creation to fail with invalid name"

def test_api_key_creation():
    api_key = client.create_api_key(TEST_API_KEY_NAME, 60)
    assert api_key is not None, "Expected API key to be created"
    assert client.api_key is not None, "Expected API key to be set after creation"

def test_get_api_key():
    key_name = client.get_api_key()
    assert key_name is not None, "Expected key to be returned"
    assert key_name == TEST_API_KEY_NAME, "Expected key to have the correct name"

def test_status():
    status = client.status()
    assert status is not None, "Expected status to be returned"
    assert isinstance(status, dict), "Expected status to be an object"
    assert 'api_key' in status, "Expected status to have an 'api_key' field"
    assert status['api_key'] == True, "Expected status to show api_key as True"

###########################
#        Use creds        #
###########################

def test_list_api_keys():
    keys = client.list_api_keys()
    assert keys is not None, "Expected keys to be returned"
    assert isinstance(keys, list), "Expected keys to be a list"
    for key in keys:
        assert isinstance(key, dict), "Expected each key to be an object"
        assert 'key_name' in key, "Expected each key to have an 'key_name' field"

def test_list_models():
    models = client.list_models()
    assert models is not None, "Expected models to be returned"
    assert isinstance(models, list), "Expected models to be a list"
    assert len(models) > 0, "Expected at least one model to be returned"
    for model in models:
        assert isinstance(model, dict), "Expected each model to be an object"
        assert 'id' in model, "Expected each model to have an 'id' field"

def test_list_system_prompts():
    system_prompts = client.list_system_prompts()
    assert system_prompts is not None, "Expected system prompts to be returned"
    assert isinstance(system_prompts, list), "Expected system prompts to be a list"
    assert len(system_prompts) > 0, "Expected at least one system prompt to be returned"
    for prompt in system_prompts:
        assert isinstance(prompt, dict), "Expected each prompt to be an object"
        assert 'id' in prompt, "Expected each prompt to have an 'id' field"

def test_create_system_prompt(test_ids):
    system_prompt = client.create_system_prompt(TEST_CREATE_SYSTEM_PROMPT, "New system prompt")
    assert system_prompt is not None, "system prompt was not created"
    assert isinstance(system_prompt, dict), "Expected system prompt to be an object"
    assert 'message_string' in system_prompt, "Expected system prompt to have a 'message_string' field"
    test_ids['test_prompt_id'] = system_prompt['id']

def test_delete_system_prompt(test_ids):
    response = client.delete_system_prompt(test_ids['test_prompt_id'])
    assert response is None, "Expected system prompt to be deleted"

def test_list_prompt_templates():
    prompt_templates = client.list_prompt_templates()
    assert prompt_templates is not None, "Expected prompt templates to be returned"
    assert isinstance(prompt_templates, list), "Expected prompt templates to be a list"
    assert len(prompt_templates) > 0, "Expected at least one prompt template to be returned"
    for prompt in prompt_templates:
        assert isinstance(prompt, dict), "Expected each prompt to be an object"
        assert 'id' in prompt, "Expected each prompt to have an 'id' field"

def test_fail_prompt_template():
    with pytest.raises(QuotientAIException) as exc_info:
        client.create_prompt_template(TEST_BAD_PROMPT_TEMPLATE, "Bad template A")
    assert "The template must include" in str(exc_info.value), "Expected prompt template creation to fail with invalid template"

def test_create_prompt_template(test_ids):
    prompt_template = client.create_prompt_template(TEST_CREATE_PROMPT_TEMPLATE, "Good template B")
    assert prompt_template is not None, "Prompt template was not created"
    assert isinstance(prompt_template, dict), "Expected prompt template to be an object"
    assert 'template_string' in prompt_template, "Expected prompt template to have a 'template_string' field"
    test_ids['test_template_id'] = prompt_template['id']

def test_delete_prompt_template(test_ids):
    response = client.delete_prompt_template(test_ids['test_template_id'])
    assert response is None, "Expected prompt template to be deleted"

def test_list_tasks():
    tasks = client.list_tasks()
    assert tasks is not None, "Expected tasks to be returned"
    assert isinstance(tasks, list), "Expected tasks to be a list"
    for task in tasks:
        assert isinstance(task, dict), "Expected each task to be an object"
        assert 'id' in task, "Expected each task to have an 'id' field"

def test_list_recipes():
    recipes = client.list_recipes()
    assert recipes is not None, "Expected recipes to be returned"
    assert isinstance(recipes, list), "Expected recipes to be a list"
    for recipe in recipes:
        assert isinstance(recipe, dict), "Expected each recipe to be an object"
        assert 'id' in recipe, "Expected each recipe to have an 'id' field"

def test_create_recipe(test_ids):
    recipe = client.create_recipe(name="Test recipe", description="Test recipe description", model_id=1, prompt_template_id=2)
    assert recipe is not None, "Recipe was not created"
    assert isinstance(recipe, dict), "Expected recipe to be an object"
    assert 'id' in recipe, "Expected recipe to have an 'id' field"
    test_ids['test_recipe_id'] = recipe['id']

def test_delete_recipe(test_ids):
    response = client.delete_recipe(test_ids['test_recipe_id'])
    assert response is None, "Expected recipe to be deleted"

def test_list_jobs():
    jobs = client.list_jobs()
    assert jobs is not None, "Expected jobs to be returned"
    assert isinstance(jobs, list), "Expected jobs to be a list"
    for job in jobs:
        assert isinstance(job, dict), "Expected each job to be an object"
        assert 'id' in job, "Expected each job to have an 'id' field"

def test_create_job(test_ids):
    job = client.create_job(task_id=2, recipe_id=1, num_fewshot_examples=2, limit=1)
    assert job is not None, "Job was not created"
    assert isinstance(job, dict), "Expected job to be an object"
    assert 'id' in job, "Expected job to have an 'id' field"
    test_ids['test_job_id'] = job['id'] 

def test_filter_by_job_id(test_ids):
    jobs = client.list_jobs(filters={'id': test_ids['test_job_id']})
    for job in jobs:
        assert 'status' in job, "Expected each job to have a 'status' field"
        assert job['status'] == "Scheduled", "Expected job to have status Scheduled"

def test_create_job_rate_limit(test_ids):
    # Assuming the rate limit is 3 jobs per hour, create 3 more jobs to surpass the limit
    for _ in range(2):
        job = client.create_job(task_id=2, recipe_id=1, num_fewshot_examples=0, limit=1)
        assert job['status'] == "Scheduled", "Expected job to be created"
    with pytest.raises(QuotientAIException) as exc_info:
        client.create_job(task_id=2, recipe_id=2, num_fewshot_examples=0, limit=1)
    assert "Rate limit exceeded" in str(exc_info.value), "Expected job creation to fail with rate limit exceeded"
    
# TODO: results tests

###########################
#       Remove creds      #
###########################
        
def test_api_key_revoke():
    result = client.revoke_api_key(TEST_API_KEY_NAME)
    assert "revoked successfully" in result, "Expected API key to be revoked"

def test_signout():
    result = client.sign_out()
    assert "Sign out successful" in result, "Expected successful signout"
    assert client.token is None, "Expected token to be None after signout"

def test_remove_api_key():
    result = client.remove_api_key()
    assert result is None, "Expected successful removal of API key"
    assert client.api_key is None, "Expected API key to be None after removal"

def test_logout_status():
    status = client.status()
    assert status is not None, "Expected status to be returned"
    assert isinstance(status, dict), "Expected status to be an object"
    assert 'api_key' in status, "Expected status to have an 'api_key' field"
    assert status['api_key'] == False, "Expected status to show api_key as False"
