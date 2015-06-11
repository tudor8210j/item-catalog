# Flask, SQLAlchemy and database_setup imports
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item


#Oauth session key impports
from flask import session as login_session
import random, string


#Oauth flow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from oauth2client.client import AccessTokenCredentials


app = Flask(__name__)

# Load the 'client_secrets.json file'
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Bind the database engine
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Create the Database session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Set the secret_key value for the session
app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
state = app.secret_key

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Login and authorize via Google
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Output login details
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You Are Now Logged In As %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions for authorization
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Logout and disconnect from Google
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        flash('You Have Been Logged Out')

        return redirect(url_for('showCategories'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Public and private home page
@app.route('/')
@app.route('/categories')
def showCategories():
    category = session.query(Category).order_by(Category.name.asc()).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(10)
    if 'username' not in login_session:
        return render_template('publicHome.html', category=category, items=items)
    return render_template('privateHome.html', category=category, items=items)

# Public and private category list
@app.route('/category/<int:category_id>/list')
def showCategory(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).order_by(Item.name.asc())
    if 'username' not in login_session:
        return render_template('category.html', category=category, items=items)
    return render_template('privateCategory.html', category=category, items=items)

# Public and proivate authorized item details
@app.route('/category/<int:category_id>/list/<int:item_id>/details')
def showItemDetails(category_id, item_id):
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()
    if 'username' not in login_session or item.user_id != login_session['user_id']:
        return render_template('itemDetails.html', category=category, item=item)
    else:
        return render_template('privateitemDetails.html', category=category, item=item)

# Private new item creation
@app.route('/category/<int:category_id>/new/',methods=['GET','POST'])
def newItem(category_id):
  category = session.query(Category).filter_by(id = category_id).one()
  if request.method == 'POST':
      newItem = Item(name = request.form['name'], category_id = category_id, description= request.form['description'], user_id = login_session['user_id'])
      session.add(newItem)
      session.commit()
      flash('New Item %s Successfully Created' % (newItem.name))
      return redirect(url_for('showCategory', category_id = category_id))
  else:
      return render_template('newItem.html', category_id = category_id)

# Private authorized edit an item
@app.route('/category/<int:category_id>/list/<int:item_id>/edit', methods=['GET','POST'])
def editItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id = item_id).one()
    if 'username' not in login_session or editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit it.');}</script><body onload='myFunction()''>"
    else:
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash('Menu Item Successfully Edited')
            return redirect(url_for('showCategory', category_id = category_id))
        else:
            return render_template('editItem.html', category_id = category_id, item_id = item_id, i = editedItem)

# Private authorized delete and item
@app.route('/category/<int:category_id>/list/<int:item_id>/delete', methods = ['GET','POST'])
def deleteItem(category_id, item_id):
    itemToDelete = session.query(Item).filter_by(id = item_id).one()
    if 'username' not in login_session or itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own item in order to delete it.');}</script><body onload='myFunction()''>"
    else:
        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
            return redirect(url_for('showCategory', category_id = category_id))
        else:
            return render_template('deleteItem.html', category_id = category_id, item_id = item_id, i = itemToDelete)

# API Endpoints

# Return all restaurants via an API
@app.route('/categories/JSON')
def categoriesJSON():
    category = session.query(Category).all()
    return jsonify(categories= [i.serialize for i in category])

# Return items in a category via an API
@app.route('/category/<int:category_id>/list/JSON')
def categoryJson(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).order_by(Item.name.asc())
    return jsonify(categoryItems=[i.serialize for i in items])

# Return a specific item in a category via an API
@app.route('/category/<int:category_id>/list/<int:item_id>/details/JSON')
def showItemDetailsJSON(category_id, item_id):
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()
    return jsonify(item = item.serialize)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
