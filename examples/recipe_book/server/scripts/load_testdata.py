#!/usr/bin/env python3

import json
import click
import requests
import random
import string


def random_string():
    return(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))

def dump_json(var):
    s = json.dumps(
        var,
        indent=2,
        sort_keys=True
    )
    return(s)

def do_graphql(url, query):
    r = requests.post(
                      url,
                      data=query,
                      headers = {'Content-type': 'application/graphql'}
    )
    print(r.status_code)
    print(r.text)
    return(json.loads(r.text))

def get_recipe(url, recipe):
    query = """query {
  recipes (name: "%(name)s", category: "%(type)s") {
    edges {
      node {
        id
        name
      }
    }
  }
}""" % recipe
    print(query)
    return(do_graphql(url, query))

def create_recipe(url, recipe):
    mutation = """mutation {
  addRecipe (name: "%(name)s", category: "%(type)s", cookTime: %(cook_time)s) {
    success
  }
}""" % recipe

    print(mutation)
    return(do_graphql(url, mutation))

def get_ingredient(url, ingredient_name):
    query = """query {
  ingredients (name: "%(ingredient_name)s") {
    edges {
      node {
        id
        name
      }
    }
  }
}""" % locals()
    print(query)
    return(do_graphql(url, query))

def create_ingredient(url, ingredient_name):
    mutation = """mutation {
  addIngredient (name: "%(ingredient_name)s") {
    success
  }
}""" % locals()

    print(mutation)
    return(do_graphql(url, mutation))


@click.command()
@click.option('--count', default=1, help='Number of iterations.')
@click.option('--random/--no-random', default=False, help='Add random string to name')
@click.option('--fname', default='recipes.json', prompt='JSON file to load',
              help='The JSON file that contains the entries to load')
@click.option('--url', default='http://localhost:8000/graphql',
              prompt='URL of the Nautilus API service',
              help='The API service tp connect to')
def load_data(count, fname, url, random):
    recipes = json.loads(open(fname).read())
    while count > 0:
        for recipe in recipes:
            if random:
                recipe['name'] = random_string() + " " + recipe['name']
            result = get_recipe(url, recipe)
            data = result.get("data")
            errors = result.get("errors")
            if errors:
                print("<<<ERROR>>>")
                print(dump_json(errors))
                continue
            if data['recipes']['edges']:
                print(("continue", data['recipes']['edges']))
                continue
            result = create_recipe(url, recipe)
            data = result.get("data")
            errors = result.get("errors")
            if errors:
                print("<<<ERROR Creating recipe>>>")
                print(dump_json(errors))
            elif not data['addRecipe']['success']:
                print("<<<ERROR No success creating recipe>>>")
            else:
                continue
            print("<<<RETRY create recipe>>>""")
            result = create_recipe(url, recipe)
           
        for recipe in recipes:
            result = get_recipe(url, recipe)
            data = result.get("data")
            errors = result.get("errors")
            if errors:
                print("<<<ERROR>>>")
                print(dump_json(errors))
                continue
            if not data['recipes']['edges']:
                print("<<<ERROR>>>, cannot find recipe %(name)s for ingredient" % recipe)
                continue
            for ingredient_name in recipe['ingredients']:
                result = get_ingredient(url, ingredient_name)
                data = result.get("data")
                errors = result.get("errors")
                if errors:
                    print("<<<ERROR>>>")
                    print(dump_json(errors))
                    continue
                if data['ingredients']['edges']:
                    continue
                create_ingredient(url, ingredient_name)
           
        count -= 1


if __name__ == "__main__":
    load_data()
