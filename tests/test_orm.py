#!/usr/bin/env python3

from os import path
import shutil
import unittest

import plyvel

import levelorm
from levelorm.fields import String, Boolean

dbpath = path.join(path.dirname(path.abspath(__file__)), 'testdb')
db = plyvel.DB(dbpath, create_if_missing=True)
DBBaseModel = levelorm.db_base_model(db)

def tearDownModule():
	shutil.rmtree(dbpath)

class Animal(DBBaseModel):
	prefix = 'animal'
	name = String(key=True)
	otomotopeia = String()
	shouts = Boolean()

class TestLevelORM(unittest.TestCase):
	def test_basic(self):
		before = Animal('cow', 'moo', shouts=True)
		before.save()
		after = Animal.get('cow')
		assert before.name == after.name == 'cow'
		assert before.otomotopeia == after.otomotopeia == 'moo'
		assert before.shouts == after.shouts == True

		animals = list(Animal.iter())
		assert len(animals) == 1
		assert animals[0] == before

	def test_str(self):
		a = Animal('sheep', 'baa', False)
		assert str(a) == "Animal(name='sheep', otomotopeia='baa', shouts=False, _key='sheep')"

	def test_eq(self):
		a = Animal('dog', 'woof', False)
		assert a != 1
