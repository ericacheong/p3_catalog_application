# project.py

from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask_bootstrap import Bootstrap
from userhelper import createUser, getUserInfo, getUserID

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

from functools import wraps
from flask import g

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

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



@app.route('/')
@app.route('/catalog/')
def latestItems():
    categories = session.query(Category).all()
    items = session.query(Item).order_by("create_time desc").limit(10)
    return render_template('catalog.html', categories=categories, items=items)

@app.route('/catalog/<int:category_id>/')
@app.route('/catalog/<int:category_id>/items/')
def showCategoryItems(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id = category.id).all()
    
    if 'username' not in login_session or category.user_id != login_session['user_id']:
        return render_template('publiccategory.html', categories=categories, 
            category=category, items=items)
    else:
        return render_template('category.html', categories=categories, 
            category=category, items=items)

@app.route('/catalog/<int:category_id>/<int:item_id>/')
def showItemDescription(category_id, item_id):
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session or item.user_id != login_session['user_id']:
        return render_template('publicitem.html', item=item, 
        categories=categories, category=category)
    else:
        return render_template('item.html', item=item, 
            categories=categories, category=category)

@app.route('/catalog/<int:category_id>/add/', methods=['GET', 'POST'])
@login_required
def addItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = Item(name = request.form['name'], 
                       description = request.form['description'],
                       category_id = category.id,
                       user_id = login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New item added.")
        return redirect(url_for('showCategoryItems', category_id=category_id))
    else:
        return render_template('additem.html', category=category)

@app.route('/catalog/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
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
        return redirect(url_for('showItemDescription', category_id=category_id, 
            item_id=editedItem.id))
    else:
        return render_template('edititem.html', category=category, 
            item=editedItem, categories=categories)

@app.route('/catalog/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    deleteItem = session.query(Item).filter_by(id=item_id).one()
    if deleteItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item deleted.")
        return redirect(url_for('showCategoryItems', category_id=category_id))
    else:
        return render_template('deleteitem.html', category=category, item=item)

@app.route('/catalog/add/', methods=['GET', 'POST'])
@login_required
def addCategory():
    if request.method == 'POST':
        if request.form['category']:
            newCat = Category(name = request.form['category'],
                user_id = login_session['user_id'])
            session.add(newCat)
            session.commit()
            flash("Category added.")
        return redirect(url_for('showCategoryItems', category_id=newCat.id))
    else:
        return render_template('addcat.html')

@app.route('/catalog/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    editCat = session.query(Category).filter_by(id=category_id).one()
    if editCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this category.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editCat.name = request.form['name']
            session.add(editCat)
            session.commit()
            flash("Category edited.")
        return redirect(url_for('showCategoryItems', category_id=editCat.id))
    else:
        return render_template('editcat.html', category=editCat)

@app.route('/catalog/<int:category_id>/delete/', methods=['GET','POST'])
@login_required
def deleteCategory(category_id):
    deleteCat = session.query(Category).filter_by(id=category_id).one()
    unclassified = session.query(Category).filter(Category.name == 'Unclassified').one()
    if deleteCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this category.'); window.location='/catalog/'}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        # Unclassified cannot be deleted
        if category_id == unclassified.id:
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
        return render_template('deletecat.html', category=deleteCat)

@app.route('/catalog/<int:category_id>/items/JSON/')
def categoryJSON(category_id):
    catItems = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(CategoryItems=[i.serialize for i in catItems])

@app.route('/catalog/<int:category_id>/<int:item_id>/JSON/')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
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