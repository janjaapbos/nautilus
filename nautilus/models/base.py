# external imports
import peewee

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
# local imports
from nautilus import admin
from ..db import db

class _Meta(type):
    """
        The base metaclass for the nautilus models. Currently, it's primary use is to
        automatically register a model class with the admin after it is created.
    """

    def __init__(self, name, bases, attributes, **kwds):
        # create the super class
        super().__init__(name, bases, attributes, **kwds)
        # if the class is not a nautilus base class
        if 'nautilus_base' not in attributes or not attributes['nautilus_base']:
            # perform the necessary functions
            self.onCreation()

        return

class _MixedMeta(_Meta, type(peewee.Model)):
    """
        This meta class mixes the sqlalchemy model meta class and the nautilus one.
    """


class BaseModel(peewee.Model, metaclass=_MixedMeta):

    nautilus_base = True # necessary to prevent meta class behavior on this model

    def __init__(self, **kwargs):
        """ treat kwargs as attribute assignment """
        # loop over the given kwargs
        for key, value in kwargs.items():
            # treat them like attribute assignments
            setattr(self, key, value)

    def _json(self):
        # build a dictionary out of just the columns in the table
        return {
            column.name: getattr(self, column.name) \
                for column in type(self).columns()
        }

    class Meta:
        database = db


    @classmethod
    def onCreation(cls): pass


    @classmethod
    def primary_key(cls):
        return cls._meta.primary_key

    @classmethod
    def required_fields(cls):
        return [field for field in cls.fields() if not field.null]

    @classmethod
    def fields(cls):
        return cls._meta.fields.values()



    __abstract__ = True

