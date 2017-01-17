from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, session as login_session
from flask import make_response, url_for, flash
from db_schema import Base, User, Category, Item
import random
import string
import httplib2
import db_access
import json
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# various methods for creating flash messages to the user
def createErrorFlash(message):
    errorFlash = ('<div class="col-12 error-flash"><strong>%s</strong></div>'
                  % message)
    return errorFlash


def createSuccessFlash(message):
    goodFlash = ('<div class="col-12 success-flash"><strong>%s</strong></div>'
                 % message)
    return goodFlash


def loginError():
    flash(createErrorFlash("You must be logged in to access that page."))
    return redirect('/gateway')


def itemError(item_id):
    flash(createErrorFlash("An item with ID '%s' does not exist!" % item_id))
    return redirect('/')


def unAuthorizedError():
    flash(createErrorFlash("You are not authorized to access that page!"))
    return redirect('/')


def getLoggedInUser():
    stored_credentials = login_session.get('credentials')
    if stored_credentials is not None:
        user = db_access.getUser(login_session['user_id'])
        if not user:
            return gdisconnect()
        return user
    return None


@app.route('/')
@app.route('/<int:category_id>')
def WelcomePage(category_id=0):
    # try to get the category to display
    try:
        category_id = int(category_id)
    except:
        return redirect('/')

    # find all items in the category specified, or get all items if category
    # doesn't exist
    items = []
    category = db_access.getCategoryById(category_id)
    if category:
        items = db_access.getItemsByCategory(category_id)
    else:
        items = db_access.getAllItems()
    categories = db_access.getAllCategories()
    return render_template("home.html",
                           user=getLoggedInUser(),
                           categories=categories,
                           items=items,
                           display_category=category_id)


@app.route('/gateway')
def LoginPage():
    user = getLoggedInUser()
    # disconeect user if they are already logged in, otherwise display login
    # page
    if user is not None:
        return gdisconnect()
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        return render_template('loginpage.html', STATE=state)


@app.route('/createitem', methods=['GET', 'POST'])
def createItem():
    user = getLoggedInUser()
    if not user:
        return loginError()

    if request.method == 'POST':
        # get data from the form and put it in the database
        name = request.form['itemName']
        description = request.form['itemDescription']
        price = request.form['itemPrice']
        category_id = request.form['itemCategory']
        user_id = user.id

        item = Item(name=name, description=description,
                    price=price, category_id=category_id, user_id=user_id)

        db_access.createItem(item)

        flash(createSuccessFlash("Item created successfully!"))
        return redirect('/')
    else:
        # display create page to user
        categories = db_access.getAllCategories()
        return render_template("createItem.html",
                               user=user,
                               categories=categories)


@app.route('/items/<int:item_id>')
def itemPage(item_id):
    user = getLoggedInUser()
    item = db_access.getItemById(item_id)
    if not item:
        # no item exists, display error
        return itemError(item_id)
    else:
        return render_template("itemPage.html", user=user, item=item)


@app.route('/items/<int:item_id>/json')
def itemJson(item_id):
    item = db_access.getItemById(item_id)
    if not item:
        # no item exists dispaly error
        return itemError(item_id)

    return jsonify(item.serialize)


@app.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])
def editItem(item_id):
    user = getLoggedInUser()
    # make sure user is logged in
    if not user:
        return loginError()
    item = db_access.getItemById(item_id)
    # make sure the requested item exists
    if not item:
        return itemError(item_id)
    # make sure logged in user is item creator
    if item.user_id != user.id:
        return unAuthorizedError()

    # all verification passed, allow the update
    if request.method == 'POST':
        item.name = request.form['itemName']
        item.description = request.form['itemDescription']
        item.price = request.form['itemPrice']
        item.category_id = request.form['itemCategory']

        db_access.updateItem(item)
        flash(createSuccessFlash("Item updated successfully!"))
        return redirect('/items/' + str(item_id))
    else:
        # display edit page
        categories = db_access.getAllCategories()
        return render_template("editItem.html",
                               user=user, item=item, categories=categories)


@app.route('/items/delete/<int:item_id>')
def deleteItem(item_id):
    # make sure user is logged in
    user = getLoggedInUser()
    if not user:
        return loginError()
    # make sure item exists
    item = db_access.getItemById(item_id)
    if not item:
        return itemError()
    # make sure user is item creator
    if item.user_id != user.id:
        return unAuthorizedError()

    # delete the item and redirect
    db_access.deleteItem(item_id)
    flash(createSuccessFlash("Item deleted successfully!"))
    return redirect('/')


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Make sure state is valid
    if request.args.get('state') != login_session['state']:
        state = ''.join(
            random.choice(
                string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('loginpage.html', STATE=state)

    code = request.data

    # exchange one time use key for long-lasting token
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response("Failed to upgrade code to token.", 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # make sure we got data from the request to google
    if result.get('error') is not None:
        response = make_response(result.get('error'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # make sure user returned from request is the correct user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            "Token's user ID doesn't match given user ID.", 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # make sure the data is meant for us
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            "Token's client ID doesn't match app's client ID.", 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gpus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gpus_id:
        response = make_response("The user is already logged in.", 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # login was successful and data looks good, store data
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    userId = db_access.getUserId(login_session['email'])

    # create user if one doesn't exist
    if not userId:
        userId = db_access.createUser(login_session)

    login_session['user_id'] = userId

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += (
        '" style="width:300px;height:300px;border-radius:150px;'
        '-webkit-border-radius:150px;-moz-border-radius:150px;">')
    return output


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is not None:
        url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
               % credentials)
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
    try:
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
    except:
        pass

    return redirect('/')


if __name__ == '__main__':
    app.secret_key = "super secret key"
    app.debug = False
    app.run(host='0.0.0.0', port=8000)
