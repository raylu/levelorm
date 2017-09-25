#!/usr/bin/env python3

from os import path
import shutil
import typing

import plyvel

import levelorm
from levelorm.fields import String, Blob, Boolean, Integer, Array
from levelorm.orm import InvalidModel
from .base import BaseTest

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

class JISAnimal(DBBaseModel):
	prefix = 'jisanimal'
	name = String(key=True, encoding='utf-16')
	onomatopoeia = String(encoding='shift-jis')

class Numbers(DBBaseModel):
	prefix = 'numbers'
	name = String(key=True)
	numbers = Array(Integer())

class Matrices(DBBaseModel):
	prefix = 'matrix'
	name = String(key=True)
	numbers = Array(Array(Integer()))

class TodoList(DBBaseModel):
	prefix = 'todo'
	name = String(key=True)
	numbers = Array(String())

class RawData(DBBaseModel):
	prefix = 'raw'
	key = Blob(key=True)
	data = Blob()

class TestLevelORM(BaseTest):
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

	def test_unicode(self):
		牛 = Animal('牛', 'もーもー', shouts=False)
		牛.save()
		assert Animal.get('牛') == 牛

		犬 = JISAnimal('犬', 'わんわん')
		犬.save()
		assert JISAnimal.get('犬') == 犬
		animals = list(JISAnimal.iter(start='犬'))
		assert len(animals) == 1
		assert animals[0] == 犬

	def test_blob(self):
		deadbeef = RawData(b'\xde\xad\xbe\xef', b'deadbeef')
		deadbeef.save()
		assert RawData.get(b'\xde\xad\xbe\xef') == deadbeef
		data = list(RawData.iter())
		assert len(data) == 1
		assert data[0] == deadbeef

	def test_invalid_model(self):
		# pylint: disable=unused-variable

		with self.assert_raises(InvalidModel):
			class NoKey(DBBaseModel):
				prefix = 'nokey'
				not_a_key = String()

		with self.assert_raises(InvalidModel):
			class MultiKey(DBBaseModel):
				prefix = 'multikey'
				key1 = String(key=True)
				key2 = Blob(key=True)

		with self.assert_raises(InvalidModel):
			class IntKey(DBBaseModel):
				prefix = 'intkey'
				key = Integer(key=True)

		with self.assert_raises(InvalidModel):
			class NoPrefix(DBBaseModel):
				key = String(key=True)
