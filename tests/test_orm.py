#!/usr/bin/env python3

from os import path
import shutil
import typing
import unittest

import plyvel

import levelorm
from levelorm.fields import String, Boolean, Integer, Array

dbpath = path.join(path.dirname(path.abspath(__file__)), 'testdb')
db = plyvel.DB(dbpath, create_if_missing=True)
DBBaseModel: typing.Any = levelorm.db_base_model(db)

def tearDownModule():
	shutil.rmtree(dbpath)

class Animal(DBBaseModel):
	prefix = 'animal'
	name = String(key=True)
	onomatopoeia = String()
	shouts = Boolean()

class Numbers(DBBaseModel):
	prefix = 'numbers'
	name = String(key=True)
	numbers = Array(Integer())

class Matrices(DBBaseModel):
	prefix = 'matrices'
	name = String(key=True)
	numbers = Array(Array(Integer()))

class TodoList(DBBaseModel):
	prefix = 'todo'
	name = String(key=True)
	numbers = Array(String())

class TestLevelORM(unittest.TestCase):
	def test_basic(self):
		before = Animal('cow', 'moo', shouts=True)
		before.save()
		after = Animal.get('cow')
		assert before.name == after.name == 'cow'
		assert before.onomatopoeia == after.onomatopoeia == 'moo'
		assert before.shouts == after.shouts == True

		dog = Animal('dog', 'woof', False)
		dog.save()
		animals = list(Animal.iter())
		assert len(animals) == 2
		assert animals[0] == before
		assert animals[1] == dog

		animal_keys = list(Animal.iter(include_value=False))
		assert animal_keys == ['cow', 'dog']

		dog_after = list(Animal.iter(start='dog'))[0]
		assert dog == dog_after

	def test_str(self):
		a = Animal('sheep', 'baa', False)
		assert str(a) == "Animal(name='sheep', onomatopoeia='baa', shouts=False)"

	def test_eq(self):
		a = Animal('dog', 'woof', False)
		assert a != 1

	def test_array(self):
		fib = Numbers('fibonacci', [1, 1, 2, 3, 5, 8])
		fib.save()
		assert Numbers.get('fibonacci') == fib

		hankel = Matrices('hankel', [
			[1, 2, 3, 4, 5],
			[2, 3, 4, 5, 6],
			[3, 4, 5, 6, 7],
			[4, 5, 6, 7, 8],
			[5, 6, 7, 8, 9],
		])
		hankel.save()
		assert Matrices.get('hankel') == hankel

		todo1 = TodoList('1', ['wash the dishes', 'charm snakes'])
		todo1.save()
		assert TodoList.get('1') == todo1
