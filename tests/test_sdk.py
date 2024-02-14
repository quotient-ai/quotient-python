import pytest
from supabase import create_client
from quotientai import QuotientClient 

from .constants import TEST_USER_EMAIL, TEST_INVALID_PASSWORD, TEST_USER_PASSWORD, TEST_API_KEY_NAME, TEST_BAD_PROMPT_TEMPLATE, TEST_CREATE_PROMPT_TEMPLATE, TEST_USER_ID, SUPABASE_URL, SUPABASE_ADMIN_KEY

client = QuotientClient()

test_template_id = None
test_recipe_id = None
test_job_id = None

###########################
#      Without creds      #
###########################

def test_invalid_credentials():
    with pytest.raises(Exception) as exc_info:
        client.login(TEST_USER_EMAIL, TEST_INVALID_PASSWORD)

def test_api_key_failure():
    with pytest.raises(Exception) as exc_info:
        client.create_api_key(TEST_API_KEY_NAME, 60)

###########################
#       Create creds      #
###########################
        
def test_successful_login():
    result = client.login(TEST_USER_EMAIL, TEST_USER_PASSWORD)
    assert "Login successful" in result, "Login unsuccessful"
    assert client.token is not None, "Expected token to be set after login"

def test_api_key_creation():
    assert client.token is not None, "Expected user to be logged in for key creation"
    api_key = client.create_api_key(TEST_API_KEY_NAME, 60)
    assert api_key is not None, "API key was not created"
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
    for model in models:
        assert isinstance(model, dict), "Expected each model to be an object"
        assert 'id' in model, "Expected each model to have an 'id' field"

def test_list_prompt_templates():
    prompt_templates = client.list_prompt_templates()
    assert prompt_templates is not None, "Expected prompt templates to be returned"
    assert isinstance(prompt_templates, list), "Expected prompt templates to be a list"
    for prompt in prompt_templates:
        assert isinstance(prompt, dict), "Expected each prompt to be an object"
        assert 'id' in prompt, "Expected each prompt to have an 'id' field"

def test_fail_prompt_template():
    with pytest.raises(Exception) as exc_info:
        client.create_prompt_template(TEST_BAD_PROMPT_TEMPLATE, "Bad template A")
    if hasattr(exc_info.value, 'status_code') and exc_info.value.status_code == 500:
        pytest.fail("Encountered 500 error during test: Is the eval server running?")

def test_create_prompt_template():
    prompt_template = client.create_prompt_template(TEST_CREATE_PROMPT_TEMPLATE, "Good template B")
    assert prompt_template is not None, "Prompt template was not created"
    assert isinstance(prompt_template, dict), "Expected prompt template to be an object"
    assert 'template_string' in prompt_template, "Expected prompt template to have a 'template_string' field"
    global test_template_id 
    test_template_id = prompt_template['id']

def test_delete_prompt_template():
    response = client.delete_prompt_template(test_template_id)
    assert f"Prompt template Good template B deleted" in response, "Expected prompt template to be deleted"

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

def test_create_recipe():
    recipe = client.create_recipe(name="Test recipe", description="Test recipe description", model_id=1, prompt_template_id=2)
    assert recipe is not None, "Recipe was not created"
    assert isinstance(recipe, dict), "Expected recipe to be an object"
    assert 'id' in recipe, "Expected recipe to have an 'id' field"
    global test_recipe_id 
    test_recipe_id = recipe['id']

def test_delete_recipe():
    response = client.delete_recipe(test_recipe_id)
    assert f"Recipe Test recipe deleted" in response, "Expected recipe to be deleted"

def test_list_jobs():
    jobs = client.list_jobs()
    assert jobs is not None, "Expected jobs to be returned"
    assert isinstance(jobs, list), "Expected jobs to be a list"
    for job in jobs:
        assert isinstance(job, dict), "Expected each job to be an object"
        assert 'id' in job, "Expected each job to have an 'id' field"

def test_create_job():
    job = client.create_job(task_id=2, recipe_id=1, num_fewshot_examples=2, limit=1)
    assert job is not None, "Job was not created"
    assert isinstance(job, dict), "Expected job to be an object"
    assert 'id' in job, "Expected job to have an 'id' field"
    global test_job_id 
    test_job_id = job['id']
    
# def test_results():
#     results = client.get_eval_results(test_job_id)
#     assert results is not None, "Expected results to be returned"
#     assert isinstance(results, dict), "Expected results to be an object"
#     assert 'id' in results, "Expected results to have an 'id' field"
#     assert results['id'] == test_job_id, "Expected results to have the correct id"

###########################
#       Remove creds      #
###########################
        
def test_api_key_revoke():
    result = client.revoke_api_key(TEST_API_KEY_NAME)
    assert "revoked successfully" in result, "Expected API key to be revoked"
    assert client.api_key is None, "Expected API key to be None after revocation"

def test_list_unauthorized():
    with pytest.raises(Exception) as exc_info:
        client.list_models()

def test_signout():
    result = client.sign_out()
    assert "Sign out successful" in result, "Expected successful signout"
    assert client.token is None, "Expected token to be None after signout"

def test_remove_api_key():
    result = client.remove_api_key()
    assert "API key removed" in result, "Expected successful removal of API key"
    assert client.api_key is None, "Expected API key to be None after removal"

def test_logout_status():
    status = client.status()
    assert status is not None, "Expected status to be returned"
    assert isinstance(status, dict), "Expected status to be an object"
    assert 'api_key' in status, "Expected status to have an 'api_key' field"
    assert status['api_key'] == False, "Expected status to show api_key as False"

###########################
#         Cleanup         #
###########################
    
def teardown_module(module):
    """Cleanup function to run after all tests in this module."""
    client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)  # Ensure this function gets your client correctly
    response = client.table('profile').select('id').eq('uid', TEST_USER_ID).execute()
    profile_id = response.data[0]['id']
    client.table('api_keys').delete().eq('user_id', TEST_USER_ID).execute()
    client.table('job').delete().eq('owner_profile_id', profile_id).execute()
    print("SDK tests cleanup completed")