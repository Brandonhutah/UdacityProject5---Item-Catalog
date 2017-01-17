Project 4 - Item Catalog

What is it?
-------------
This project practices using the Flask and SqlAlchemy frameworks to interact with the user and the data. It also uses Google's OAuth service to provide secure login functionality to users.
Once logged in, users can create, edit, and delete items from various different categories.

To Run
-------------
If this is your first time running the program, start at step 1. Otherwise skip to step 3.

1) Navigate to /vagrant/catalog and run the python script 'db_schema.py using the command 'python db_schema.py'. This will create an empty database for the project.

2) Then you will want to run the python script 'populate_categories.py' in the same directory using the command 'python populate_categories.py'. This will populate the database with different categories for items.

3) In the directory '/vagrant/catalog' run the python script 'web_server.py' using the command 'python web_server.py'. Once this is running, you can navigate to the website by browsing to 'http://localhost:8000'