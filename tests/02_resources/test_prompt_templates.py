import os

import pytest

from quotientai import QuotientAIException


def test_list_prompt_templates(quotient_client):
    prompt_templates = quotient_client.list_prompt_templates()
    assert prompt_templates is not None, "Expected prompt templates to be returned"
    assert isinstance(prompt_templates, list), "Expected prompt templates to be a list"
    assert (
        len(prompt_templates) > 0
    ), "Expected at least one prompt template to be returned"
    for prompt in prompt_templates:
        assert isinstance(prompt, dict), "Expected each prompt to be an object"
        assert "id" in prompt, "Expected each prompt to have an 'id' field"


def test_fail_prompt_template(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_prompt_template(
            os.getenv("TEST_BAD_PROMPT_TEMPLATE"), "Bad template A"
        )
    assert "The template must include" in str(
        exc_info.value
    ), "Expected prompt template creation to fail with invalid template"


def test_create_prompt_template(quotient_client, keyring):
    prompt_template = quotient_client.create_prompt_template(
        os.getenv("TEST_CREATE_PROMPT_TEMPLATE"), "Good template B"
    )
    assert prompt_template is not None, "Prompt template was not created"
    assert isinstance(prompt_template, dict), "Expected prompt template to be an object"
    assert (
        "template_string" in prompt_template
    ), "Expected prompt template to have a 'template_string' field"
    keyring["test_template_id"] = prompt_template["id"]


def test_delete_prompt_template(quotient_client, keyring):
    response = quotient_client.delete_prompt_template(keyring["test_template_id"])
    assert response is None, "Expected prompt template to be deleted"


# Check that prompt template is deleted
def test_prompt_template_deleted(quotient_client, keyring):
    prompt_templates = quotient_client.list_prompt_templates(
        filters={"id": keyring["test_template_id"]}
    )
    assert prompt_templates is not None, "Expected prompt templates to be returned"
    assert keyring["test_template_id"] not in [
        template["id"] for template in prompt_templates
    ], "Expected created prompt template to not be in the list"
