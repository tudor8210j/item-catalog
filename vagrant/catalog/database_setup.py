# Import required modules
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Create User base and table
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

# Create Category base and table
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Serialize the category table to be used for JSON API endpoints
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

# Create Item base and table
class Item(Base):
    """Declares necessary Item columns and table name."""

    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # Serialize the item table to be used for JSON API endpoints
    @property
    def serialize(self):
        """Returns object data in easily serializable format."""

        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id
        }


# Initializes the database
engine = create_engine('sqlite:///catalog.db')

# Binds new database to Base
Base.metadata.create_all(engine)
