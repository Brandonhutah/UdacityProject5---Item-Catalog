from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_schema import Base, User, Category, Item


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# CRUD operations for User Table
def createUser(login_session):
    user = User(name=login_session['username'], email=login_session[
                'email'], picture=login_session['picture'])
    session.add(user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUser(userId):
    try:
        user = session.query(User).filter_by(id=userId).one()
        return user
    except:
        return None


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def updateUser(newUserData):
    return


def deleteUser(userId):
    return

# CRUD operations for Category Table


def createCategory(name):
    category = Category(name=name)
    session.add(category)
    session.commit()
    category = session.query(Category).filter_by(name=name).one()
    return category.id


def getCategoryById(categoryId):
    try:
        category = session.query(Category).filter_by(id=categoryId).one()
        return category
    except:
        return None


def getCategoryByName(name):
    try:
        category = session.query(Category).filter_by(name=name).one()
        return category
    except:
        return None


def getAllCategories():
    categories = session.query(Category).all()
    return categories


# CRUD operations for Item Table
def createItem(item):
    session.add(item)
    session.commit()
    newItem = session.query(Item).filter_by(name=item.name).one()
    return newItem.id


def updateItem(item):
    session.add(item)
    session.commit()


def getAllItems():
    items = session.query(Item).order_by(Item.name).all()
    return items


def getItemsByCategory(category_id):
    items = session.query(Item).filter_by(
        category_id=category_id).order_by(Item.name).all()
    return items


def getItemById(item_id):
    try:
        item = session.query(Item).filter_by(id=item_id).one()
        return item
    except:
        return None


def deleteItem(item_id):
    item = getItemById(item_id)
    session.delete(item)
    session.commit()
