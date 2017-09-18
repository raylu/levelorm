import collections
import io
from typing import Iterator, List, Type, TypeVar, Union

import plyvel

from . import fields

class ModelMeta(type):
	@classmethod
	def __prepare__(mcs, name, bases, **kwds):
		if len(bases) == 1 and bases[0].__name__ == 'DBBaseModel':
			# order the class's fields so we can init with positional args
			return collections.OrderedDict()
		else:
			return type.__prepare__(mcs, name, bases, **kwds)

	def __new__(mcs, clsname, bases, namespace, **kwds):
		result = type.__new__(mcs, clsname, bases, dict(namespace))

		# only set _fields for subclasses of DBBaseModel
		if len(bases) == 1 and bases[0].__name__ == 'DBBaseModel':
			all_fields = []
			keyname = None
			for name, field in namespace.items():
				if not isinstance(field, fields.BaseField):
					continue
				all_fields.append(name)
				if field.key:
					if keyname is not None:
						raise Exception('%s has multiple keys; %r and %r' % (clsname, keyname, name))
					if not isinstance(field, fields.String):
						raise Exception('keys must be Strings bug %s is %s' % (name, field.__class__))
					keyname = name
			if keyname is None:
				raise Exception('%s has no key' % clsname)

			result._fields = tuple(all_fields)
			result._keyname = keyname
		return result

Model = TypeVar('Model', bound='BaseModel')

class BaseModel(metaclass=ModelMeta):
	'''
	base model for ``DBBaseModel`` to inherit from.
	user models should inherit from a class created by :meth:`levelorm.db_base_model`
	'''

	db: plyvel.DB = None
	prefix: str = None

	_keyname: str
	_fields: List[str]

	def __init__(self, *args, **kwargs) -> None:
		num_args = len(args) + len(kwargs)
		if num_args != len(self._fields):
			raise TypeError('%s has %d fields but %d arguments were given' %
					(self.__class__.__name__, len(self._fields), num_args))

		for i, value in enumerate(args):
			setattr(self, self._fields[i], value)
		for fieldname, value in kwargs.items():
			if fieldname not in self._fields:
				raise TypeError('%s got an unexpected keyword argument %r' %
						(self.__class__.__name__, fieldname))
			setattr(self, fieldname, value)

		self._key = getattr(self, self._keyname)

	def save(self) -> None:
		'''
		writes this instance to the :attr:`db`.
		members are serialized in the order they are defined on the model and are 4-byte aligned
		'''
		buf = io.BytesIO()
		for fieldname in self._fields:
			if fieldname == self._keyname:
				continue
			field = getattr(self.__class__, fieldname)
			value = getattr(self, fieldname)
			field.serialize(buf, value)

			# alignment
			remainder = buf.tell() % 4
			if remainder != 0:
				padding = 4 - remainder
				buf.write(b'\0' * padding)

		keyfield = getattr(self.__class__, self._keyname)
		self.db.put(self._key.encode(keyfield.encoding), buf.getvalue())

	def __repr__(self) -> str:
		args = []
		for fieldname in self._fields:
			args.append('%s=%r' % (fieldname, getattr(self, fieldname)))
		return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

	def __eq__(self, other):
		try:
			for fieldname in self._fields:
				value = getattr(self, fieldname)
				if value != getattr(other, fieldname):
					return False
		except AttributeError:
			return False
		return True

	@classmethod
	def get(cls: Type[Model], key: str) -> Model:
		''' return an instance of the model by querying :attr:`db` and parsing the result '''
		keyfield = getattr(cls, cls._keyname)
		data = cls.db.get(key.encode(keyfield.encoding))
		if data is None:
			return None
		return cls.parse(key, data)

	@classmethod
	def parse(cls: Type[Model], key: str, data: bytes) -> Model:
		''' used internally by :meth:`get` and :meth:`iter` to deserialize values '''
		buf = io.BytesIO(data)
		kwargs = {cls._keyname: key}
		for fieldname in cls._fields:
			if fieldname == cls._keyname:
				continue
			field = getattr(cls, fieldname)
			kwargs[fieldname] = field.deserialize(buf)

			# alignment
			remainder = buf.tell() % 4
			if remainder != 0:
				padding = 4 - remainder
				buf.seek(padding, io.SEEK_CUR)
		return cls(**kwargs)

	@classmethod
	def iter(cls: Type[Model], **kwargs) -> Iterator[Union[Model, str]]:
		'''
		proxies to `plyvel.DB.iterator <https://plyvel.readthedocs.io/en/latest/api.html#iterator>`_
		but yields ``(str, BaseModel)`` pairs instead of ``(bytes, bytes)``
		'''
		keyfield = getattr(cls, cls._keyname)
		if 'start' in kwargs:
			kwargs['start'] = kwargs['start'].encode(keyfield.encoding)
		if 'stop' in kwargs:
			kwargs['stop'] = kwargs['stop'].encode(keyfield.encoding)

		if kwargs.get('include_value', True):
			with cls.db.iterator(**kwargs) as it:
				for key, data in it:
					yield cls.parse(key.decode(keyfield.encoding), data)
		else:
			with cls.db.iterator(**kwargs) as it:
				for key in it:
					yield key.decode(keyfield.encoding)

def db_base_model(db: plyvel.DB) -> Type[BaseModel]:
	'''
	create a base model class that all user models should inherit from.
	the returned base class holds a reference to the ``plyvel.DB``
	'''
	def __init_subclass__(cls):
		if not cls.prefix:
			raise Exception('models must have prefixes')
		cls.db = db.prefixed_db(('%s-' % cls.prefix).encode('utf-8'))
	base_model = type('DBBaseModel', (BaseModel,), {'__init_subclass__': __init_subclass__})
	return base_model
