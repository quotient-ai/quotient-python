import pytest
from supabase import create_client
from click.testing import CliRunner
import os
from quotientai import cli 

from .constants import TEST_USER_EMAIL, TEST_USER_PASSWORD, TEST_API_KEY_NAME, TEST_CREATE_PROMPT_TEMPLATE, TEST_USER_ID, SUPABASE_URL, SUPABASE_ADMIN_KEY

runner = CliRunner()
test_api_key = None

@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # Setup code here [later?]
    yield
    del os.environ['QUOTIENT_KEY']
    client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
    response = client.table('profile').select('id').eq('uid', TEST_USER_ID).execute()
    if not response.data:
        print("No profile found for test user: Cleanup not done")
        return
    profile_id = response.data[0]['id']
    client.table('api_keys').delete().eq('user_id', TEST_USER_ID).execute()
    client.table('prompt_template').delete().eq('owner_profile_id', profile_id).execute()
    print("CLI tests cleanup completed")
    
def test_authentication_flow():
    inputs = f"{TEST_USER_PASSWORD}\n{TEST_API_KEY_NAME}\n30\n"
    result = runner.invoke(cli, ['authenticate', '--email', TEST_USER_EMAIL], input=inputs)
    global test_api_key
    test_api_key = result.output.split('\n')[-2].strip()
    os.environ['QUOTIENT_KEY'] = test_api_key
    assert result.exit_code == 0
    assert 'Login successful! Now to set an API key.' in result.output
    assert 'API keys are only returned once' in result.output
    assert 'Set the API key as environment variable QUOTIENT_KEY' in result.output
    assert test_api_key is not None, "Expected API key to be returned"

def test_get_api_key():
    result = runner.invoke(cli, ['auth', 'get_key'])
    assert result.exit_code == 0
    assert TEST_API_KEY_NAME in result.output

def test_list_api_keys():
    result = runner.invoke(cli, ['list', 'api-keys'])
    assert result.exit_code == 0
    assert TEST_API_KEY_NAME in result.output
    
def test_list_models():
    """Test listing models without filters."""
    result = runner.invoke(cli, ['list', 'models'])
    assert result.exit_code == 0
    assert "llama-2-7b-chat" in result.output

def test_list_datasets():
    """Test listing datasets without filters."""
    result = runner.invoke(cli, ['list', 'datasets'])
    assert result.exit_code == 0
    assert "squad_v2" in result.output

def test_list_templates():
    """Test listing templates without filters."""
    result = runner.invoke(cli, ['list', 'prompt-templates'])
    assert result.exit_code == 0
    assert "Question Answering" in result.output 

def create_prompt_template():
    result = runner.invoke(cli, ['create', 'prompt-template', '--name', "Good template B", '--template', TEST_CREATE_PROMPT_TEMPLATE])
    assert result.exit_code == 0
    assert "Good template B" in result.output

def test_list_tasks():
    """Test listing tasks without filters."""
    result = runner.invoke(cli, ['list', 'tasks'])
    assert result.exit_code == 0
    assert "squad-v2" in result.output

def test_list_recipes():
    """Test listing recipes without filters."""
    result = runner.invoke(cli, ['list', 'recipes'])
    assert result.exit_code == 0
    assert "llama-question" in result.output

def test_revoke_api_key():
    result = runner.invoke(cli, ['auth', 'revoke_key', '--key_name', TEST_API_KEY_NAME])
    assert result.exit_code == 0
    assert "revoked successfully" in result.output
