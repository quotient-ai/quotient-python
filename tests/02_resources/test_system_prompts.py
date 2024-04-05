import os


def test_list_system_prompts(quotient_client):
    system_prompts = quotient_client.list_system_prompts()
    assert system_prompts is not None, "Expected system prompts to be returned"
    assert isinstance(system_prompts, list), "Expected system prompts to be a list"
    assert len(system_prompts) > 0, "Expected at least one system prompt to be returned"
    for prompt in system_prompts:
        assert isinstance(prompt, dict), "Expected each prompt to be an object"
        assert "id" in prompt, "Expected each prompt to have an 'id' field"


def test_create_system_prompt(quotient_client, keyring):
    system_prompt = quotient_client.create_system_prompt(
        os.getenv("TEST_CREATE_SYSTEM_PROMPT"), "New system prompt"
    )
    assert system_prompt is not None, "system prompt was not created"
    assert isinstance(system_prompt, dict), "Expected system prompt to be an object"
    assert (
        "message_string" in system_prompt
    ), "Expected system prompt to have a 'message_string' field"
    keyring["test_prompt_id"] = system_prompt["id"]


def test_delete_system_prompt(quotient_client, keyring):
    response = quotient_client.delete_system_prompt(keyring["test_prompt_id"])
    assert response is None, "Expected system prompt to be deleted"


def test_system_prompt_deleted(quotient_client, keyring):
    system_prompts = quotient_client.list_system_prompts(
        filters={"id": keyring["test_prompt_id"]}
    )
    assert system_prompts is not None, "Expected system prompts to be returned"
    assert keyring["test_prompt_id"] not in [
        prompt["id"] for prompt in system_prompts
    ], "Expected created system prompt to not be in the list"
