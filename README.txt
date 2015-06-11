Program Name: Item Catalog
Programmer: Jon Tudor
Purpose: To enable an item catalog website that has full CRUD functionality with a SQLAlchemy database and full authentication and authorization capabilities through Google +.
Verion: 1.0

Quick Start:
- In order to install this program , first clone the repository.
- Once cloned navigate to the vagrant directory in the cloned directory and bring up a VM with the command "vagrant up". (Please note you will need VM ware installed to do this).
- Once the VM is up SSH into the VM with the command "vagrant ssh" and then navigate the /vagrant/catalog folder.
- Run the command "python application.py" to start the application with the default database contents. To access the home page of the application navigate to "http://localhost:8000" in the browser of your choice.
- If you wish to start with a clean database delete the database_setup.pyc file and then run the "python database_setup.pyc" command.

Note: To enable proper Google + authentication you will need to run the below commands from the /vagrant/catalog directory on the VM if you have newer versions of the below software.
sudo pip install werkzeug==0.8.3
sudo pip install flask==0.9
sudo pip install Flask-Login==0.1.3

Intended Functions of the Application:
- All page visitors can view all catagories, items and item details.
- Users authenticated through their Google + account can create new items and edit and delete their own items and item descriptions.

Authentication and Authorization Permissions:
- Users who are not logged in can view the publicHome, category, itemDetails and login pages.
- Users who are logged in can see the above plus privateHome, privateCategory, and newItem pages.
- Users who are logged in can see the privateitemDetails, deleteItem, and editItem pages for their own items.
