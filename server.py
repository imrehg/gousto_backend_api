"""Simple recipe server"""
import csv
import math
from flask import Flask, Response, request, abort, jsonify

## HTTP Results Code (could use external module for this, but defining now for simplicity)
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405

# Pagination size of the search pages
PAGE_SIZE = 10

def load_database(filename):
    """Load database from a CSV file

    Args:
        filename: the filename of the database

    Returns:
        dictionary containing application data
    """
    database = {}
    with open(filename) as csvfile:
        recipereader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in recipereader:
            database[row['id']] = row
    return database

# The application database, as simple as it gets
DB = load_database('recipe-data.csv')

###
# The server
###

app = Flask(__name__)

### Helper functions

def paginate(results, page):
    """Paginate a list of results

    Args:
        results: a list of results
        page: the specific page to get

    Globals:
        PAGE_SIZE: the pagination size

    Returns:
        a tuple consisting of a list of results
        from a given page (defined by the page size),
        and the an integer giving the highes passible page
        number given the list of results
    """
    paginated_results = [result for index, result in enumerate(results) if page * PAGE_SIZE <= index < (page + 1) * PAGE_SIZE]
    last_page = math.ceil(len(results) / PAGE_SIZE) - 1 if len(results) > 0 else 0
    return paginated_results, last_page

###
# Routes
###

# Provide JSON responses to the given errors too
@app.errorhandler(400)
def resource_bad_request(e):
    return jsonify(error=str(e)), HTTP_BAD_REQUEST

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), HTTP_NOT_FOUND

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(error=str(e)), HTTP_METHOD_NOT_ALLOWED

@app.route('/recipe/<recipe_id>',  methods = ['GET', 'UPDATE'])
def find_recipe_by_id(recipe_id):
    """Action on recipes by ID, either to look up,
    or modify fields of.

    Args:
        recipe_id: the recipe to act upon.

    Returns:
        a response containing a recipe
    """
    # Looking up a recipe
    if request.method == 'GET':
        try:
            recipe = DB[recipe_id]
            code = HTTP_OK
            return recipe, code
        except (KeyError):
            abort(HTTP_NOT_FOUND, "No recipe by this ID.")

    # Updating a recipe
    if request.method == 'UPDATE':
        if not request.is_json:
            abort(HTTP_BAD_REQUEST, "Need JSON to update.")
        try:
            recipe = DB[recipe_id]
        except (KeyError):
            abort(HTTP_NOT_FOUND, "No recipe by this ID.")
        update_request = request.get_json()
        for field, value in update_request.items():
            if field not in recipe:
                abort(HTTP_BAD_REQUEST, f"Field not found: {field}")
            if field == "id":
                abort(HTTP_BAD_REQUEST, f"Updating the ID field is not allowed.")
            recipe[field] = value
        return recipe, HTTP_OK

@app.route('/search/by_cuisine',  methods = ['GET'])
def find_recipe_by_cuisine():
    """Query a recipe by cuisine, given by a specific
    query string.

    Query string:
        q: the query (required)
        page: the page of the paginated results to give (optional)

    Returns:
        a response containing the found results, the given page,
        and the last possible page based on the found results
    """
    if not request.args:
        abort(HTTP_BAD_REQUEST, "No query provided")

    args = request.args.to_dict()
    if 'q' in args:
        keys_to_keep = ["id", "title", "marketing_description"]
        search_results = [{f:v[f] for f in v if f in keys_to_keep} for k, v in DB.items() if v['recipe_cuisine'] == args['q']]
    else:
        abort(HTTP_BAD_REQUEST, "No query provided")

    if 'page' in args:
        try:
            page = int(args['page'])
        except ValueError:
            abort(HTTP_BAD_REQUEST, f"Invalid pagination: {args['page']}")
        if page < 0:
            abort(HTTP_BAD_REQUEST, f"Invalid pagination: {page}")
    else:
        # If no page given, return the first one
        page = 0
    # Filter to the appropriate page
    paginated_results, last_page = paginate(search_results, page)
    return {"results": paginated_results, "page": page, "last_page": last_page}
