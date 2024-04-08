import os

import pytest
from postgrest import SyncPostgrestClient

from quotientai import QuotientClient


@pytest.fixture(scope="session")
def keyring():
    keys = {
        "test_api_key": None,
        "test_model_id": None,
        "test_template_id": None,
        "test_prompt_id": None,
        "test_task_id": None,
        "test_recipe_id": None,
        "test_job_id": None,
    }
    yield keys


@pytest.fixture(scope="module", autouse=True)
def quotient_client(keyring):
    if keyring["test_api_key"] is not None:
        os.environ["QUOTIENT_API_KEY"] = keyring["test_api_key"]
    client = QuotientClient()
    yield client
    client.end_session()
    if "QUOTIENT_API_KEY" in os.environ:
        del os.environ["QUOTIENT_API_KEY"]


@pytest.fixture(scope="session", autouse=True)
def teardown_module():
    """Cleanup function to run after all tests in this module."""
    try:
        setup_client = SyncPostgrestClient(
            os.getenv("SUPABASE_URL") + "/rest/v1",
            headers={"apiKey": os.getenv("SUPABASE_ANON_KEY")},
        )
        setup_client.auth(os.getenv("SUPABASE_ADMIN_KEY"))
        setup_client.from_("api_keys").delete().eq(
            "uid", os.getenv("TEST_USER_ID")
        ).execute()
        setup_client.from_("api_keys").delete().eq(
            "uid", os.getenv("TEST_USER_ID_2")
        ).execute()
        setup_client.aclose()
    except Exception as e:
        print("Error in teardown: ", e)
    yield
    # Teardown code
    try:
        teardown_client = SyncPostgrestClient(
            os.getenv("SUPABASE_URL") + "/rest/v1",
            headers={"apiKey": os.getenv("SUPABASE_ANON_KEY")},
        )
        teardown_client.auth(os.getenv("SUPABASE_ADMIN_KEY"))
        teardown_client.from_("api_keys").delete().eq(
            "uid", os.getenv("TEST_USER_ID")
        ).execute()
        teardown_client.from_("api_keys").delete().eq(
            "uid", os.getenv("TEST_USER_ID_2")
        ).execute()
        teardown_client.aclose()
        print("SDK tests cleanup completed")
    except Exception as e:
        print("Error in cleanup: ", e)
