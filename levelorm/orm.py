import collections
import struct

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
			nonstring_fields = []
			string_fields = [] # excluding key
			keyname = None
			formatstr = ''
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
				elif isinstance(field, fields.String):
					string_fields.append(name)
				else:
					nonstring_fields.append(name)
					formatstr += field.formatstr
			if keyname is None:
				raise Exception('%s has no key' % clsname)

			result._fields = tuple(all_fields)
			result._nonstring_fields = tuple(nonstring_fields)
			result._string_fields = tuple(string_fields)
			result._keyname = keyname
			result._struct = struct.Struct(formatstr)
		return result

class BaseModel(metaclass=ModelMeta):
	db = None
	prefix = None

	def __init__(self, *args, **kwargs):
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

	def save(self):
		nonstring_values = []
		string_values = []
		for fieldname in self._nonstring_fields:
			value = getattr(self, fieldname)
			nonstring_values.append(value)
		for fieldname in self._string_fields:
			value = getattr(self, fieldname)
			string_values.append(value.encode('utf-8'))

		data = self._struct.pack(*nonstring_values) + b'\0'.join(string_values)
		self.db.put(self._key.encode('utf-8'), data)

	def __repr__(self):
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
	def get(cls, key):
		data = cls.db.get(key.encode('utf-8'))
		if data is None:
			return None
		return cls.parse(key, data)

	@classmethod
	def parse(cls, key, data):
		nonstring_values = cls._struct.unpack(data[:cls._struct.size])
		bytes_values = data[cls._struct.size:].split(b'\0')
		string_values = tuple(map(lambda v: v.decode('utf-8'), bytes_values))
		kwargs = dict(zip(cls._nonstring_fields + cls._string_fields, nonstring_values + string_values))
		kwargs[cls._keyname] = key
		return cls(**kwargs)

	@classmethod
	def iter(cls, **kwargs):
		if 'start' in kwargs:
			kwargs['start'] = kwargs['start'].encode('utf-8')
		if 'stop' in kwargs:
			kwargs['stop'] = kwargs['stop'].encode('utf-8')

		if kwargs.get('include_value', True):
			with cls.db.iterator(**kwargs) as it:
				for key, data in it:
					yield cls.parse(key.decode('utf-8'), data)
		else:
			with cls.db.iterator(**kwargs) as it:
				for key in it:
					yield key.decode('utf-8')

def db_base_model(db):
	def __init_subclass__(cls):
		if not cls.prefix:
			raise Exception('models must have prefixes')
		cls.db = db.prefixed_db(('%s-' % cls.prefix).encode('utf-8'))
	base_model = type('DBBaseModel', (BaseModel,), {'__init_subclass__': __init_subclass__})
	return base_model
