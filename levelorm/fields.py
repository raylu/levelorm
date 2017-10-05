import abc
import struct
from typing import BinaryIO

from .exceptions import InvalidModel

# pylint: disable=abstract-method

class BaseField(metaclass=abc.ABCMeta):
	'''
	every model must have exactly one :class:`String` or :class:`Blob` with ``key=True`` which will
	not be included in the value and instead used as the key
	'''

	def __init__(self, key: bool = False) -> None:
		self.key = key

	@abc.abstractmethod
	def serialize(self, buf: BinaryIO, value) -> None:
		raise NotImplementedError

	@abc.abstractmethod
	def deserialize(self, buf: BinaryIO):
		raise NotImplementedError

	def serialize_key(self, value) -> bytes:
		raise NotImplementedError

	def deserialize_key(self, value: bytes):
		raise NotImplementedError

class String(BaseField):
	''' represents a :class:`str`. stored as an unsigned 4-byte length and encoded bytes '''

	length_struct = struct.Struct('I')

	def __init__(self, encoding: str = 'utf-8', key=False) -> None:
		self.encoding = encoding
		super().__init__(key)

	def serialize(self, buf, value):
		encoded = value.encode(self.encoding)
		buf.write(self.length_struct.pack(len(encoded)) + encoded)

	def deserialize(self, buf) -> str:
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		b = buf.read(length)
		return b.decode(self.encoding)

	def serialize_key(self, value: str):
		return value.encode(self.encoding)

	def deserialize_key(self, value) -> str:
		return value.decode(self.encoding)

class Blob(BaseField):
	''' represents a :class:`bytes`. stored as an unsigned 4-byte length and bytes '''

	length_struct = struct.Struct('I')

	def serialize(self, buf, value):
		buf.write(self.length_struct.pack(len(value)) + value)

	def deserialize(self, buf) -> str:
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		return buf.read(length)

	def serialize_key(self, value: bytes):
		return value

	def deserialize_key(self, value) -> bytes:
		return value

class Boolean(BaseField):
	'''
	represents a :class:`bool`.
	stored as 1 byte (but :meth:`levelorm.orm.BaseModel.save` will pad to 4)
	'''

	struct = struct.Struct('?')

	def serialize(self, buf, value: bool):
		if not isinstance(value, bool):
			raise TypeError('expected bool, got %r' % value)
		buf.write(self.struct.pack(value))

	def deserialize(self, buf) -> bool:
		return self.struct.unpack(buf.read(self.struct.size))[0]

class Integer(BaseField):
	'''
	represents an :class:`int`.
	stored as a signed 4-byte int
	'''

	struct = struct.Struct('i')

	def serialize(self, buf, value: int):
		buf.write(self.struct.pack(value))

	def deserialize(self, buf) -> int:
		return self.struct.unpack(buf.read(self.struct.size))[0]

class Float(BaseField):
	'''
	represents a :class:`float`.
	stored as a double precision (8 byte, binary64) float
	'''

	struct = struct.Struct('d')

	def serialize(self, buf, value: float):
		buf.write(self.struct.pack(value))

	def deserialize(self, buf) -> float:
		return self.struct.unpack(buf.read(self.struct.size))[0]

class Array(BaseField):
	'''
	represents a :class:`list`.
	stored as an unsigned 4-byte length and however the inner class is serialized

	usage example: ::

		class Matrices(DBBaseModel):
			prefix = 'matrix'
			name = String(key=True)
			numbers = Array(Array(Integer()))
		identity = Matrices('identity', [[1, 0], [0, 1]])
	'''

	length_struct = struct.Struct('I')

	def __init__(self, inner: BaseField, key=False) -> None:
		if not isinstance(inner, BaseField):
			raise InvalidModel('Array inner type is not a field: %r' % (inner))
		self.inner = inner
		super().__init__(key)

	def serialize(self, buf, value: list):
		if not isinstance(value, list):
			raise TypeError('expected list, got %r' % value)
		buf.write(self.length_struct.pack(len(value)))
		for element in value:
			self.inner.serialize(buf, element)

	def deserialize(self, buf) -> list:
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		value = []
		for _ in range(length):
			value.append(self.inner.deserialize(buf))
		return value
