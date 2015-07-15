# database_setup.py

import sys
import string

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.sql import func
# from sqlalchemy_utils import PasswordType

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    name = Column(String(250))
    email = Column(String(250), nullable=False, unique=True)
    picture = Column(String(250))
    # password = Column(PasswordType(
    #     schemes=[
    #         'pbkdf2_sha512',
    #         'md5_crypt'
    #     ]))

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable = False, unique = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    description = Column(String(500))
    create_time = Column(DateTime, default=func.now())
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'create_time' : self.create_time.strftime("%B %d, %Y"),
            'description' : self.description,
            'user' : str(self.user.id)            
        }
    

engine = create_engine('sqlite:///categoryitemswithuser.db')

Base.metadata.create_all(engine)
