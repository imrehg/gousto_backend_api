import json
import pytest

import server

@pytest.fixture
def client():
    """Set up a test client"""
    with server.app.test_client() as client:
        yield client

def test_nonexistent_routed(client):
    """Request a non-existent endpoint"""
    resp = client.get('/random')
    assert resp.status_code == server.HTTP_NOT_FOUND

def test_query_recipe(client):
    """Simple query a recipe"""
    resp = client.get('/recipe/1')
    assert resp.is_json
    assert resp.get_json()['title'] == "Sweet Chilli and Lime Beef on a Crunchy Fresh Noodle Salad"

def test_query_nonexistent_recupe(client):
    """Query a recipe by a nonexistent ID"""
    resp = client.get('/recipe/1000')
    assert resp.status_code == server.HTTP_NOT_FOUND

def update_field(client, id, update):
    """Test helper to update a recipe by ID

    Args:
        client: the test client
        id: the recipe ID to update
        update: the dictionary of changes
    """
    # Get the recipe first, to be able to compare later
    resp_original = client.get(f'/recipe/{id}')
    original_recipe = resp_original.get_json()
    # Do the requested update
    resp = client.open(f'/recipe/{id}', method='UPDATE', json=update)
    assert resp.is_json
    assert resp.status_code == server.HTTP_OK
    # The response contains the updated field
    updated_recipe = resp.get_json()
    # Check that the relevant fields are all updated
    for k, v in update.items():
        assert updated_recipe[k] == v
    # Check tht other fields are still the same
    for k, v in updated_recipe.items():
        if k not in update.keys():
            assert original_recipe[k] == v
    # Check that now querying the same recipe will also retains the changes
    resp = client.get(f'/recipe/{id}')
    assert resp.is_json
    assert resp.status_code == server.HTTP_OK
    updated_recipe_get = resp.get_json()
    for k, v in update.items():
        assert updated_recipe_get[k] == update[k]

def test_update_recipe_single_field(client):
    """Test updating a field of a recipe"""
    id = 1
    update = {'title': "Peking Duck"}
    update_field(client, id, update)

def test_update_recipe_multiple_fields(client):
    """Test updating multiple fields of a recipe"""
    id=2
    update = {"title": "Marmalade Cake",
              "marketing_description": "A modern take on sponge cakes",
              "calories_kcal": 10000}
    update_field(client, id, update)

def test_update_recipe_id(client):
    """Test updating a recipe's ID"""
    resp = client.open('/recipe/1', method='UPDATE', json={'id': '2'})
    assert resp.status_code == server.HTTP_BAD_REQUEST

def test_update_recipe_invalid_field(client):
    """Test updating an invalid field"""
    resp = client.open('/recipe/1', method='UPDATE',json={'random': 'xxxx'})
    assert resp.status_code == server.HTTP_BAD_REQUEST

def test_post_recipe(client):
    """Test posting to the recipe endpoint"""
    new_title = "Peking Duck"
    resp = client.post('/recipe/1', json={'title': new_title})
    assert resp.status_code == server.HTTP_METHOD_NOT_ALLOWED

def test_delete_recipe(client):
    """Test using delete method on the recipe endpoint"""
    resp = client.delete('/recipe/1')
    assert resp.status_code == server.HTTP_METHOD_NOT_ALLOWED

def test_search_cuisine(client):
    """Test searching by cuisine"""
    resp = client.open('/search/by_cuisine', query_string={"q": "british"})
    assert resp.status_code == server.HTTP_OK
    assert resp.is_json
    response_dict = resp.get_json()
    # Only find one page worth of items
    assert response_dict['page'] == 0
    assert response_dict['last_page'] == 0
    # Know the count of results expected in the test set
    assert len(response_dict['results']) == 4
    # The first item should have this ID in the test set
    assert response_dict['results'][0]['id'] == '3'
    # Only specific fields are present
    assert sorted(response_dict['results'][0].keys()) == ['id', 'marketing_description', 'title']

def test_search_cuisine_higher_page(client):
    """Test getting results from a higher page"""
    page_number = 1
    resp = client.open('/search/by_cuisine', query_string={"q": "british", "page": page_number})
    assert resp.status_code == server.HTTP_OK
    assert resp.is_json
    response_dict = resp.get_json()
    assert response_dict['page'] == page_number
    assert len(response_dict['results']) == 0

def test_search_cuisine_nonexistent(client):
    """Test querying a cuisine that should return no results """
    resp = client.open('/search/by_cuisine', query_string={"q": "klingon"})
    assert resp.status_code == server.HTTP_OK
    assert resp.is_json
    response_dict = resp.get_json()
    assert response_dict['page'] == 0
    assert response_dict['last_page'] == 0
    assert len(response_dict['results']) == 0

def test_search_cuisine_no_query(client):
    """Test not supplying query string to cuisine query"""
    resp = client.open('/search/by_cuisine', query_string={})
    assert resp.status_code == server.HTTP_BAD_REQUEST

def test_search_cuisine_negative_page(client):
    """Test negative pagination"""
    resp = client.open('/search/by_cuisine', query_string={"q": "british", "page": -2})
    assert resp.status_code == server.HTTP_BAD_REQUEST

def test_search_cuisine_non_integer_page(client):
    """Test invvalid pagination"""
    resp = client.open('/search/by_cuisine', query_string={"q": "british", "page": "xxxx"})
    assert resp.status_code == server.HTTP_BAD_REQUEST
