def test_create_recipe(quotient_client, keyrng):
    recipe = quotient_client.create_recipe(
        name="Test recipe",
        description="Test recipe description",
        model_id=1,
        prompt_template_id=2,
    )
    assert recipe is not None, "Recipe was not created"
    assert isinstance(recipe, dict), "Expected recipe to be an object"
    assert "id" in recipe, "Expected recipe to have an 'id' field"
    keyrng["test_recipe_id"] = recipe["id"]


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


def test_delete_recipe(quotient_client, keyrng):
    response = quotient_client.delete_recipe(keyrng["test_recipe_id"])
    assert response is None, "Expected recipe to be deleted"


def test_recipe_deleted(quotient_client, keyrng):
    recipes = quotient_client.list_recipes()
    assert recipes is not None, "Expected recipes to be returned"
    assert keyrng["test_recipe_id"] not in [
        recipe["id"] for recipe in recipes
    ], "Expected created recipe to not be in the list"
