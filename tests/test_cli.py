import pytest
from supabase import create_client
from click.testing import CliRunner
import os
from quotientai import cli 

from .constants import (
    TEST_API_KEY_NAME, 
    TEST_USER_EMAIL, 
    TEST_USER_PASSWORD, 
    TEST_CREATE_PROMPT_TEMPLATE, 
    TEST_USER_ID, 
    SUPABASE_URL, 
    SUPABASE_ADMIN_KEY
)

runner = CliRunner()

###########################
#         Cleanup         #
###########################

@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # Setup code
    if 'QUOTIENT_API_KEY' in os.environ:
        del os.environ['QUOTIENT_API_KEY']
    yield
    # Teardown code
    if 'QUOTIENT_API_KEY' in os.environ:
        del os.environ['QUOTIENT_API_KEY']
    client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
    response = client.table('profile').select('id').eq('uid', TEST_USER_ID).execute()
    if not response.data:
        print("No profile found for test user: Cleanup not done")
        return
    profile_id = response.data[0]['id']
    client.table('api_keys').delete().eq('user_id', TEST_USER_ID).execute()
    client.table('prompt_template').delete().eq('owner_profile_id', profile_id).execute()
    print("CLI tests cleanup completed")

###########################
#      Without creds      #
###########################
    
def test_authentication_api_key_exists():
    # inputs = f"{TEST_USER_EMAIL}\nbadpassword\n{TEST_API_KEY_NAME}\n30\n"
    os.environ['QUOTIENT_API_KEY'] = "mock_key"
    result = runner.invoke(cli, ['authenticate'])
    assert result.exit_code == 0
    assert 'API key found in environment variables.' in result.output
    del os.environ['QUOTIENT_API_KEY']

def test_authentication_fail():
    inputs = f"{TEST_USER_EMAIL}\nbadpassword\n{TEST_API_KEY_NAME}\n30\n"
    result = runner.invoke(cli, ['authenticate'], input=inputs)
    assert result.exit_code == 0
    assert 'Login failed' in result.output

###########################
#       Create creds      #
###########################
    
def test_authentication_flow():
    inputs = f"{TEST_USER_EMAIL}\n{TEST_USER_PASSWORD}\n{TEST_API_KEY_NAME}\n30\n"
    result = runner.invoke(cli, ['authenticate'], input=inputs)
    test_api_key = result.output.split('\n')[-2].strip()
    os.environ['QUOTIENT_API_KEY'] = test_api_key
    assert result.exit_code == 0
    assert 'Login successful! Now to set an API key.' in result.output, "Expected successful login"
    assert 'API keys are only returned once' in result.output, "Expected API key warning"
    assert 'Add to your shell' in result.output, "Expected API key instructions"
    assert 'ey' in result.output, "Expected API key to be returned"
    
def test_get_api_key():
    check_api_key = os.environ.get('QUOTIENT_API_KEY')
    assert check_api_key is not None, "Expected API key to be set as environment variable"
    result = runner.invoke(cli, ['auth', 'get-key'])
    assert result.exit_code == 0
    assert TEST_API_KEY_NAME in result.output
    
###########################
#        Use creds        #
###########################

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

###########################
#       Remove creds      #
###########################

def test_revoke_api_key():
    result = runner.invoke(cli, ['auth', 'revoke-key', '--key-name', TEST_API_KEY_NAME])
    assert result.exit_code == 0
    assert "revoked successfully" in result.output

def test_list_fail():
    """Test listing recipes with invalid API key."""
    result = runner.invoke(cli, ['list', 'models'])
    assert result.exit_code == 0
    assert 'Invalid or revoked API key' in result.output
