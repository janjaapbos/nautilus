#!/bin/bash

source ./env

python3 ../recipeBook/ingredientRecipe/manage.py syncdb
python3 ../recipeBook/ingredientRecipe/manage.py runserver --host=0.0.0.0 --port=8003 --debug
