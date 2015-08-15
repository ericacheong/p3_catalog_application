# P2: Catalog Application

This program is created for the Udacity Full Stack Web Developer Nanodegree.

The project includes a database schema to store the game matches between players. Program code is written to query this data and determine the winners of various games.

## Language:
Python

## Features:
1. Users should login using Google+ or Facebook.
2. Registered users can add, edit and delete their own items.
3. Registered users can add, edit and delete their own categories.
4. When a category is deleted, all items in the category is moved to "Unclassified". The category "Unclassified" cannot be deleted.
5. JSON endpoints to categories and items. Use the following path:
```
All items in a category:
http://localhost:5000/catalog/<int:category_id>/items/JSON/
A specific item:
http://localhost:5000/catalog/<int:category_id>/<int:item_id>/JSON/
```

## Prerequisite:
1. Flask == 0.10.1
2. Flask-Login == 0.1.3
3. Python-sqlalchemy
4. oauth2client
5. requests
6. httplib2
7. sqlite
8. flask_bootstrap


## Installation:
1. Set up database. Run "python database_setup.py"
2. Load testing data. Run "python itempopulator.py"

## Usage:
1. The program includes sample data. To load sample data, run 'python itempopulator.py'
2. To start application, run 'python application.py'
3. Run http://localhost:5000 in web broswer
