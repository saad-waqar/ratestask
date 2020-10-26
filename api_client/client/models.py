from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Date, ForeignKey, Integer, Text
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import relationship

from .settings import DATABASE
from . import app


app.config["SQLALCHEMY_DATABASE_URI"] = URL(**DATABASE)
db = SQLAlchemy(app)


class Region(db.Model):
    __tablename__ = 'regions'

    slug = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    parent_slug = Column(ForeignKey('regions.slug'))

    parent = relationship('Region', remote_side=[slug])


class Port(db.Model):
    __tablename__ = 'ports'

    code = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    parent_slug = Column(ForeignKey('regions.slug'), nullable=False)

    region = relationship('Region')


t_prices = db.Table(
    'prices', db.metadata,
    Column('orig_code', ForeignKey('ports.code'), nullable=False),
    Column('dest_code', ForeignKey('ports.code'), nullable=False),
    Column('day', Date, nullable=False),
    Column('price', Integer, nullable=False)
)
