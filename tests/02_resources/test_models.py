def test_create_model(quotient_client):
    model = quotient_client.create_model(
        name="bedrock-test",
        endpoint="amazon.titan-text-lite-v1",
        description="A description for the model.",
        method="AWS",
        headers={
            "aws_access_key": "some_key",
            "aws_secret_access_key": "some_secret_key",
        },
        payload_template='{"inputText": "{input_text}", "textGenerationConfig": {"maxTokenCount": 4096, "stopSequences": [], "temperature": 0, "topP": 1}}',
        path_to_data="$.results[0].outputText",
        path_to_context=None,
    )
    assert model is not None, "Model was not created"
    assert isinstance(model, dict), "Expected model to be an object"
    assert "id" in model, "Expected model to have an 'id' field"


def test_list_models(quotient_client, keyring):
    models = quotient_client.list_models()
    assert models is not None, "Expected models to be returned"
    assert isinstance(models, list), "Expected models to be a list"
    assert len(models) > 0, "Expected at least one model to be returned"
    assert keyring["test_model_id"] in [
        model["id"] for model in models
    ], "Expected test model to be in the list"
    for model in models:
        assert isinstance(model, dict), "Expected each model to be an object"
        assert "id" in model, "Expected each model to have an 'id' field"


def test_delete_model(quotient_client):
    models = quotient_client.list_models()
    for model in models:
        if model["name"] == "bedrock-test":
            response = quotient_client.delete_model(model["id"])
            assert response is None, "Expected model to be deleted"


def test_model_deleted(quotient_client, keyring):
    models = quotient_client.list_models(filters={"id": keyring["test_model_id"]})
    assert models is not None, "Expected models to be returned"
    assert keyring["test_model_id"] not in [
        model["id"] for model in models
    ], "Expected created model to not be in the list"
