from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from db_schema import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

category1 = Category(name="Sports/Outdoors")
category2 = Category(name="Music")
category3 = Category(name="Entertainment")
category4 = Category(name="Electronics")
category5 = Category(name="Food")
category6 = Category(name="Furniture")
category7 = Category(name="Toys")

session.add(category1)
session.add(category2)
session.add(category3)
session.add(category4)
session.add(category5)
session.add(category6)
session.add(category7)

session.commit()
