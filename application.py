# project.py

from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask_bootstrap import Bootstrap

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
from flask import make_response
import requests

from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

app = Flask(__name__)
Bootstrap(app)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


engine = create_engine('sqlite:///categoryitemswithuser.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('latestItems'))
    else:
        flash("You were not logged in")
        return redirect(url_for('latestItems'))

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
        # return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# Disconnect from google login
@app.route("/gdisconnect")
def gdisconnect():
    # Only disconnect a connected user.
    # credentials = login_session.get('credentials')
    
    credentials = AccessTokenCredentials(login_session.get('credentials'), 
        'user-agent-value')
    
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    # print "access_token: " + access_token
    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        response = make_response(
            json.dumps('Failed to revoke for a given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.2/me"
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    #Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # check if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permission' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out."


# User Helper Functions

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


@app.route('/')
@app.route('/catalog/')
def latestItems():
    categories = session.query(Category).all()
    items = session.query(Item).order_by("create_time desc").limit(10)
    return render_template('catalog.html', categories=categories, items=items)

@app.route('/catalog/<category>/')
@app.route('/catalog/<category>/items/')
def showCategoryItems(category):
    categories = session.query(Category).all()
    cat = session.query(Category).filter(Category.name == category).one()
    items = session.query(Item).filter_by(category_id = cat.id).all()
    print cat.user_id
    if 'username' not in login_session or cat.user_id != login_session['user_id']:
        return render_template('publiccategory.html', categories=categories, 
            category=category, items=items)
    else:
        return render_template('category.html', categories=categories, 
            category=category, items=items)

@app.route('/catalog/<category>/<item>/')
def showItemDescription(category, item):
    categories = session.query(Category).all()
    item = session.query(Item).filter(Item.name == item).one()
    if 'username' not in login_session or item.user_id != login_session['user_id']:
        return render_template('publicitem.html', item=item, 
        categories=categories, category=category)
    else:
        return render_template('item.html', item=item, 
            categories=categories, category=category)

@app.route('/catalog/<category>/add/', methods=['GET', 'POST'])
def addItem(category):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        cat = session.query(Category).filter(Category.name == category).one()
        newItem = Item(name = request.form['name'], 
                       description = request.form['description'],
                       category_id = cat.id,
                       user_id = login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New item added.")
        return redirect(url_for('showCategoryItems', category=category))
    else:
        return render_template('additem.html', category=category)

@app.route('/catalog/<category>/<item>/edit/', methods=['GET', 'POST'])
def editItem(category, item):
    editedItem = session.query(Item).filter(Item.name == item).one()
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            flash("Item name edited.")
        if request.form['description']:
            editedItem.description = request.form['description']
            flash("Item description edited.")
        if request.form['cat']:
            selectedCat = session.query(Category).filter(
                Category.name == request.form['cat']).one()
            editedItem.category_id = selectedCat.id
            flash("Item category edited.")
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showItemDescription', category=category, 
            item=editedItem.name))
    else:
        return render_template('edititem.html', category=category, 
            item=editedItem, categories=categories)

@app.route('/catalog/<category>/<item>/delete/', methods=['GET', 'POST'])
def deleteItem(category, item):
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = session.query(Item).filter(Item.name == item).one()
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item deleted.")
        return redirect(url_for('showCategoryItems', category=category))
    else:
        return render_template('deleteitem.html', category=category, item=item)

@app.route('/catalog/add/', methods=['GET', 'POST'])
def addCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['category']:
            newCat = Category(name = request.form['category'],
                user_id = login_session['user_id'])
            session.add(newCat)
            session.commit()
            flash("Category added.")
        return redirect(url_for('showCategoryItems', category=newCat.name))
    else:
        return render_template('addcat.html')

@app.route('/catalog/<category>/edit/', methods=['GET', 'POST'])
def editCategory(category):
    if 'username' not in login_session:
        return redirect('/login')
    editCat = session.query(Category).filter(Category.name == category).one()
    if editedCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editCat.name = request.form['name']
            session.add(editCat)
            session.commit()
            flash("Category edited.")
        return redirect(url_for('showCategoryItems', category=editCat.name))
    else:
        return render_template('editcat.html', category=category)

@app.route('/catalog/<category>/delete/', methods=['GET','POST'])
def deleteCategory(category):
    if 'username' not in login_session:
        return redirect('/login')
    deleteCat = session.query(Category).filter(Category.name == category).one()
    unclassified = session.query(Category).filter(Category.name == 'Unclassified').one()
    if deleteCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        # Unclassified cannot be deleted
        if category == 'Unclassified':
            flash("Category Unclassified cannot be deleted.")
            return redirect(url_for('latestItems'))
        else: 
            # move all items under deleteCat to unclassified
            deleteCatItems = session.query(Item).filter_by(category_id = deleteCat.id).all()
            for d in deleteCatItems:
                d.category_id = unclassified.id
                session.add(d)
                session.commit()
                flash("Category deleted.")
            session.delete(deleteCat)
            session.commit()
            return redirect(url_for('latestItems'))
    else:
        return render_template('deletecat.html', category=category)

@app.route('/catalog/<category>/items/JSON/')
def categoryJSON(category):
    cat = session.query(Category).filter(Category.name == category).one()
    catItems = session.query(Item).filter_by(category_id = cat.id).all()
    return jsonify(CategoryItems=[i.serialize for i in catItems])

@app.route('/catalog/<category>/<item>/JSON/')
def itemJSON(category, item):
    item = session.query(Item).filter(Item.name == item).one()
    return jsonify(Item = item.serialize)

# Atom feed helper function
def make_external(url):
    return urljoin(request.url_root, url)

@app.route('/catalog/recent.atom/')
def recent_feed():
    feed = AtomFeed('Recent Items',
                    feed_url=request.url, url=request.url_root)
    items = session.query(Item).order_by("create_time desc").limit(10)
    for item in items:
        feed.add(item.name, item.description,
                 content_type='html', id=item.id,
                 updated=item.create_time)

    return feed.get_response()

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)