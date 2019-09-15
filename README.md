# Simple recipes server

This repository implements the **Backend API Technical Challenge** as outlined in the [Backend API Technical Challenge - Instructions](./Backend API Technical Challenge - Instructions.pdf) file.

## Outline

The implementation uses the [Flask](https://palletsprojects.com/p/flask/) web framework, and runnin a [Gunicorn](https://gunicorn.org) WSGI HTTP Server in front of it (not stricktly required, but in the spirit of the challenge, closer to production deployment).

The server is deployed using [Docker](https://www.docker.com).

## Usage

There are 2 main ways to run the server:

* locally running through Flask
* building it as a Docker container, running containerized

### Locally running through Flask

* should ensure that you have at least Python 3.7 and `pip` installed.
* likely you want to set up a local virtualenv
```
virtualenv venv
sourve venv/bin/activate
```
* install the runtime requirements with
```
pip install -r requirements.txt
```
* start up the server with
```
FLASK_APP=server.py flask run --port 8000
```
Then you can `CTRL-C` to stop the server and `deactivate` the virtualenv when finished.

To run the tests:
* stop the server, if running
* install the testing requirements with
```
pip install -r requirements_test.txt
```
* run the tests simply with
```
pytest
```

### Running containerized

Build the container with the provided `Dockerfile` by running
```
docker build -t recipe_server .
```
(can change the resulting image name to anything from `recipe_server`, but for clarity's sake that's what the rest of the readme is using)


To run the tests, execute:
```
docker run recipe_server test
```

To run the server, either start it interactively:
```
docker run -p 8000 -ti recipe_server
```
and then can stop the service with a `CTRL-C`, or run detached
```
docker run -d --name recipes recipe_server
```
and then can stop it easily using the container name (set to `recipes` above, but can be anything else as required)
```
docker stop recipes
```

## Interacting with the server

In both cases, the server listens to port `8000` (so that it doesn't have to run privileged, as it would be the case on the regular HTTP(S) ports, for simplicity in the challenge's case). To query the server, use `curl` for example

```
~> curl --silent  "http://localhost:8000/search/by_cuisine?q=mexican"  | jq .
{
  "last_page": 0,
  "page": 0,
  "results": [
    {
      "id": "10",
      "marketing_description": "Comprising all the best bits of the classic American number and none of the mayo, this is a warm & tasty chicken and bulgur salad with just a hint of Scandi influence. A beautifully summery medley of flavours and textures",
      "title": "Pork Katsu Curry"
    }
  ]
}
```

## Functionality

### Use Case 1: As an API client I want to see a recipe's details

Use a `GET` request to `/recipe/<id>` to query a recipe by the `<id>`:

```
~> curl --silent  "http://localhost:8000/recipe/1"  | jq .
{
  "base": "noodles",
  "box_type": "vegetarian",
  "bulletpoint1": "",
  "bulletpoint2": "",
  "bulletpoint3": "",
  "calories_kcal": "401",
  "carbs_grams": "0",
  "created_at": "30/06/2015 17:58:00",
  "equipment_needed": "Appetite",
  "fat_grams": "35",
  "gousto_reference": "59",
  "id": "1",
  "in_your_box": "",
  "marketing_description": "Here we've used onglet steak which is an extra flavoursome cut of beef that should never be cooked past medium rare. So if you're a fan of well done steak, this one may not be for you. However, if you love rare steak and fancy trying a new cut, please be",
  "origin_country": "Great Britain",
  "preparation_time_minutes": "35",
  "protein_grams": "12",
  "protein_source": "beef",
  "recipe_cuisine": "asian",
  "recipe_diet_type_id": "meat",
  "season": "all",
  "shelf_life_days": "4",
  "short_title": "",
  "slug": "sweet-chilli-and-lime-beef-on-a-crunchy-fresh-noodle-salad",
  "title": "Sweet Chilli and Lime Beef on a Crunchy Fresh Noodle Salad",
  "updated_at": "30/06/2015 17:58:00"
}
```

## Use Case 2: As an API client I want to see a paginated list of recipes by cuisine

Use a `GET` request to `/search/by_cuisine?q=<cuisine>(&page=<page>)` search by `<cuisine>`, and optionally paginate:

```
~> curl --silent  "http://localhost:8000/search/by_cuisine?q=italian"  | jq .
{
  "last_page": 0,
  "page": 0,
  "results": [
    {
      "id": "2",
      "marketing_description": "Tamil Nadu is a state on the eastern coast of the southern tip of India. Curry from there is particularly famous and it's easy to see why. This one is brimming with exciting contrasting tastes from ingredients like chilli powder, coriander and fennel seed",
      "title": "Tamil Nadu Prawn Masala"
    },
    {
      "id": "8",
      "marketing_description": "A Goustofied British institution, learn how to make beautifully golden breaded chicken escalopes drizzled in homemade garlic butter and served atop fluffy potato and broccoli mash.",
      "title": "Homemade Eggs & Beans"
    }
  ]
}
```

The items found are returned as list within `results`. The reply also includes the current `page` number, and also the `last_page` value, which should be the largest page value with results using the given pagination, and can be used by the client to see if it needs to make any more requests.

The example data set does not contain enough test cases to actually paginate with the challenge's 10-results-per-page setting, but one can replace `recipe-data.csv` with a larger dataset and try.

The use case description says that

> each recipe has to contain only the fields ID, title and description

but this somewhat ambiguous, as there is a `title` field but no `description`, only `marketing_description`. Thus if things are not exactly defined, one also thinks whether the right field returned is `title` or the also present `short_title`? This would need tighter spec for clarity.

## Use Case 3: As an API client I want to update one or more recipe's fields

To update a field, send a `PATCH` request with a JSON payload containing the changes as `{"field": "value"}`, to `/recipe/<id>`.

```
# Check the original value
~> curl --silent "http://localhost:8000/recipe/5"  | jq '.title, .season, .recipe_cuisine'
"Fennel Crusted Pork with Italian Butter Beans"
"all"
"british"

# Do an update to some fields, check that only the requested fields are updated, and the updated record is returned
~> curl --silent -X PATCH --header "Content-Type: application/json"  -d '{"title": "Baked Alaska", "season": "winter"}' http://localhost:8000/recipe/5 | jq '.title, .season, .recipe_cuisine'
"Baked Alaska"
"winter"
"british"

# Re-requesting the same recipe will show the updated values from here on
~> curl --silent "http://localhost:8000/recipe/5"  | jq '.title, .season, .recipe_cuisine'
"Baked Alaska"
"winter"
"british"
```

Here the specification wasn't completely clear whether it is required to update multiple recipe in the same time, and not just multiple fields. Thus made an opinionated choice to only allow a single recipe to be updated at a time, but multiple (valid) fields at a time. This is because I think
* the format of the multi-recipe-multi-field update is not clearly defined in the spec (e.g. is it same fields across all, or can be different fields for each?)
* the spec called for returning the updated recipe fields, but in a similar spirit as the earlier "search" functionality that is paged, on a single `PATCH` one could not return paged results (otherwise might end up with really large responses, if updating a lot of recipes)
* the multi-recipe updates should be implemented on the client side iterating through the relevant `<id>` values (some more on this in the next section)

## Improvements and additional functionality

Currently the **pagination is hardcoded**, this could be either a parameter set at server start time, or could be also variable (within ranges), if the API would be defined such as providing results not by `page`, but `limit` (how many results returned in one request), and  `start` value (from where to count up to that many items), with also returning the total count of potential search results. The `limit` can be variable withing some provided limits (say "up to X" records).

The **search page** is a very simple implementation curently working only for the `recipe_cuisine` field, as the use case requested. This is partly so that the API model does not need to expose the exact field names (such as `/search/by_cuisine` can be redone with no client changes, if `recpie_cuisine` in the database is changed due any requirements). This also applies to any other fields as well, that while a more generic search field can be implemented naively by just querying a `/search` endpoint with `?recipe_cuisine=british&season=all` to get results for multiple fields, but that exposes the internal structure which cannot then change without client change. Also, some of the fields have types that are ideally queried in more complex ways, such as numerical fields (e.g. `calories_kcal`, `shelf_life_days`) where less-than/greater-than would make sense; fields where membership test might be good (e.g. `in_your_box`); fields where date comparison might be useful `created_at`. Thus likely the best way to implement a robust search would be to have a more complex query functionality in an unified `/search` endpoint.

Requesting **pages beyond the search results**, ie. ones that are so high value that there are no more data available, the response will not have an HTTP error code here, just simply empty result list is returned and the client can check that or see that `page` is larger than `last_page`. This is a relaxed behaviour, but not necessarily the best. In some cases it might be useful to provide an different behaviour (most likely returning HTTP code 404 - not found) if the page is beyond the available search results.

When doing a recipe update, **the `updated_at` field is not updated**, which is beyond the minimal spec, obviously, but likely would be good to do. For that the date fields would need to be treated as proper dates.

The **recipe update doesn't allow changing the <id> field**, which wasn't in the spec, but it seemed like that would be too much of a "shoot yourself in the foot" possibility, and this it errors with a 400 Bad Request. Also, not in the spec, but updating non-existend fields results in a similar error.

The **update endpoint uses the field names directly**, and as mentioned on the `/search/by_cuisine` section, that is not a good way to tie external interface to the data model. Likely a decoupled updater API would be the best, which can translate between the externally exposed names/values and the internal storage model.

The **update one by one is likely quite slow** as mentioned above, so a better spec is likely required, and thus this endpoint would be different, maybe accepting input such as `{id1: {field1: value1, ...}, id2: {field2: value2, ...}}` with a `PATCH` at e.g. a `/recipe`. Here this would require more information on corner cases, such as what happens if any of the recipe updates fails - should the whole update fail (i.e atomic behaviour) or just the given single one; or more info regarding the update format as well, whether it's in a limited form of "list of ids, and these same field changes on all of them".

There is **no authentication** on the update endpoint at the moment, that should not be like that in practice, but requests should be authenticated.

There's **no recipe creation/deletion endpoint** at the moment, these chould be added as extra `POST` requests on `/recipe` and `DELETE` on `/recipe/<id>` endpoints

## Extra information
