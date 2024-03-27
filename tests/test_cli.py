import os

import pytest
from click.testing import CliRunner
from postgrest import SyncPostgrestClient

from quotientai import cli

runner = CliRunner()


admin_client = SyncPostgrestClient(
    os.getenv("SUPABASE_URL") + "/rest/v1",
    headers={"apiKey": os.getenv("SUPABASE_ANON_KEY")},
)
admin_client.auth(os.getenv("SUPABASE_ADMIN_KEY"))


###########################
#      Setup/Cleanup      #
###########################


def get_profile_id():
    try:
        response = (
            admin_client.from_("profile")
            .select("id")
            .eq("uid", os.getenv("TEST_USER_ID"))
            .execute()
        )
        if not response.data:
            raise ValueError("No profile found for test user")
        return response.data[0]["id"]
    except Exception as e:
        print("Error getting profile ID: ", e)


def get_items_by_profile_id(table, profile_id):
    try:
        response = (
            admin_client.from_(table)
            .select("*")
            .eq("owner_profile_id", profile_id)
            .execute()
        )
        if not response.data:
            raise ValueError("No item found for profile id")
        return response.data
    except Exception as e:
        print(f"Error getting {table} by profile ID ({profile_id}): ", e)


@pytest.fixture(scope="module")
def test_ids():
    keys = {
        "test_profile_id": None,
        "test_api_key_id": None,
        "test_prompt_template_id": None,
        "test_system_prompt_id": None,
    }
    yield keys


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # Setup code
    if "QUOTIENT_API_KEY" in os.environ:
        del os.environ["QUOTIENT_API_KEY"]
    yield
    # Teardown code
    try:
        if "QUOTIENT_API_KEY" in os.environ:
            del os.environ["QUOTIENT_API_KEY"]
        admin_client.from_("api_keys").delete().eq(
            "user_id", os.getenv("TEST_USER_ID")
        ).execute()
        print("CLI tests cleanup completed")
    except Exception as e:
        print("CLI tests cleanup failed: ", e)


###########################
#      Without creds      #
###########################


def test_authentication_api_key_exists():
    os.environ["QUOTIENT_API_KEY"] = "mock_key"
    result = runner.invoke(cli, ["authenticate"])
    assert result.exit_code == 0
    assert "API key found in environment variables." in result.output
    del os.environ["QUOTIENT_API_KEY"]


def test_authentication_fail():
    inputs = f"{os.getenv('TEST_USER_EMAIL')}\nbadpassword\n{os.getenv('TEST_API_KEY_NAME')}\n30\n"
    result = runner.invoke(cli, ["authenticate"], input=inputs)
    assert result.exit_code == 0
    assert "Login failed" in result.output


###########################
#       Create creds      #
###########################


def test_authentication_flow(test_ids):
    inputs = f"{os.getenv('TEST_USER_EMAIL')}\n{os.getenv('TEST_USER_PASSWORD')}\n{os.getenv('TEST_API_KEY_NAME')}\n30\n"
    result = runner.invoke(cli, ["authenticate"], input=inputs)
    test_api_key = result.output.split("\n")[-2].strip()
    os.environ["QUOTIENT_API_KEY"] = test_api_key
    assert result.exit_code == 0
    assert (
        "Login successful! Now to set an API key." in result.output
    ), "Expected successful login"
    assert (
        "API keys are only returned once" in result.output
    ), "Expected API key warning"
    assert "Add to your shell" in result.output, "Expected API key instructions"
    assert "ey" in result.output, "Expected API key to be returned"
    # Get user information for the rest of the tests
    profile_id = get_profile_id()
    test_ids["test_profile_id"] = profile_id


def test_get_api_key():
    check_api_key = os.environ.get("QUOTIENT_API_KEY")
    assert (
        check_api_key is not None
    ), "Expected API key to be set as environment variable"
    result = runner.invoke(cli, ["auth", "get-key"])
    assert result.exit_code == 0
    assert os.getenv("TEST_API_KEY_NAME") in result.output


###########################
#        Use creds        #
###########################


def test_list_api_keys():
    result = runner.invoke(cli, ["list", "api-keys"])
    assert result.exit_code == 0
    assert os.getenv("TEST_API_KEY_NAME") in result.output


def test_list_models():
    """Test listing models without filters."""
    result = runner.invoke(cli, ["list", "models"])
    assert result.exit_code == 0
    assert "Llama-2-7b-chat" in result.output


def test_list_datasets():
    """Test listing datasets without filters."""
    result = runner.invoke(cli, ["list", "datasets"])
    assert result.exit_code == 0
    assert "squad_v2" in result.output


def test_list_prompts():
    """Test listing system prompts without filters."""
    result = runner.invoke(cli, ["list", "system-prompts"])
    assert result.exit_code == 0
    assert "Default System Prompt" in result.output


def test_create_system_prompt(test_ids):
    result = runner.invoke(
        cli,
        [
            "create",
            "system-prompt",
            "--name",
            "Good system prompt",
            "--message-string",
            os.getenv("TEST_CREATE_SYSTEM_PROMPT"),
        ],
    )
    assert result.exit_code == 0
    assert "Good system prompt" in result.output
    # Get the system prompt ID for cleanup
    sp_id = get_items_by_profile_id("system_prompt", test_ids["test_profile_id"])
    test_ids["test_system_prompt_id"] = sp_id[0]["id"]


def test_list_templates():
    """Test listing templates without filters."""
    result = runner.invoke(cli, ["list", "prompt-templates"])
    assert result.exit_code == 0
    assert "Question Answering" in result.output


def test_create_prompt_template(test_ids):
    result = runner.invoke(
        cli,
        [
            "create",
            "prompt-template",
            "--name",
            "Good template B",
            "--template",
            os.getenv("TEST_CREATE_PROMPT_TEMPLATE"),
        ],
    )
    assert result.exit_code == 0
    assert "Good template B" in result.output
    # Get the prompt template ID for cleanup
    pt_id = get_items_by_profile_id("prompt_template", test_ids["test_profile_id"])
    test_ids["test_prompt_template_id"] = pt_id[0]["id"]


def test_list_tasks():
    """Test listing tasks without filters."""
    result = runner.invoke(cli, ["list", "tasks"])
    assert result.exit_code == 0
    assert "squad-v2" in result.output


def test_list_recipes():
    """Test listing recipes without filters."""
    result = runner.invoke(cli, ["list", "recipes"])
    assert result.exit_code == 0
    assert "llama-question" in result.output


def test_delete_system_prompt(test_ids):
    sp_id = test_ids["test_system_prompt_id"]
    result = runner.invoke(
        cli, ["delete", "system-prompt", "--system-prompt-id", sp_id]
    )
    assert result.exit_code == 0
    assert "Removed system prompt" in result.output


def test_delete_prompt_template(test_ids):
    result = runner.invoke(
        cli,
        [
            "delete",
            "prompt-template",
            "--prompt-template-id",
            test_ids["test_prompt_template_id"],
        ],
    )
    assert result.exit_code == 0
    assert "Removed prompt template" in result.output


###########################
#       Remove creds      #
###########################


def test_revoke_api_key():
    result = runner.invoke(
        cli, ["auth", "revoke-key", "--key-name", os.getenv("TEST_API_KEY_NAME")]
    )
    assert result.exit_code == 0
    assert "revoked successfully" in result.output


def test_list_fail():
    """Test listing recipes with invalid API key."""
    result = runner.invoke(cli, ["list", "models"])
    assert result.exit_code == 0
    assert "Invalid or revoked API key" in result.output
