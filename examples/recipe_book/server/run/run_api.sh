#!/bin/bash

source ./env

python3 ../recipeBook/api/manage.py syncdb
python3 ../recipeBook/api/manage.py runserver --host=0.0.0.0 --port=8000 --debug
