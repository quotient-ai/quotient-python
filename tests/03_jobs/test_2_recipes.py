import pytest

from quotientai import QuotientAIException


def test_create_recipe(quotient_client, keyring):
    recipe = quotient_client.create_recipe(
        name="Test recipe",
        description="Test recipe description",
        model_id=1,
        prompt_template_id=2,
    )
    assert recipe is not None, "Recipe was not created"
    assert isinstance(recipe, dict), "Expected recipe to be an object"
    assert "id" in recipe, "Expected recipe to have an 'id' field"
    keyring["test_recipe_id"] = recipe["id"]


def test_list_recipes(quotient_client, keyring):
    recipes = quotient_client.list_recipes()
    assert recipes is not None, "Expected recipes to be returned"
    assert isinstance(recipes, list), "Expected recipes to be a list"
    assert len(recipes) > 0, "Expected at least one recipe to be returned"
    assert keyring["test_recipe_id"] in [
        recipe["id"] for recipe in recipes
    ], "Expected created recipe to be in the list"
    for recipe in recipes:
        assert isinstance(recipe, dict), "Expected each recipe to be an object"
        assert "id" in recipe, "Expected each recipe to have an 'id' field"


def test_cannot_create_duplicate_recipe(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_recipe(
            name="Test recipe",
            description="Test recipe description",
            model_id=1,
            prompt_template_id=2,
        )
    assert "Recipe with the same name already exists" in str(
        exc_info.value
    ), "Expected recipe creation to fail with duplicate name"


def test_delete_recipe(quotient_client, keyring):
    response = quotient_client.delete_recipe(keyring["test_recipe_id"])
    assert response is None, "Expected recipe to be deleted"


def test_recipe_deleted(quotient_client, keyring):
    recipes = quotient_client.list_recipes()
    assert recipes is not None, "Expected recipes to be returned"
    assert keyring["test_recipe_id"] not in [
        recipe["id"] for recipe in recipes
    ], "Expected created recipe to not be in the list"
