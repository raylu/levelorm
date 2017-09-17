import abc
import struct
from typing import BinaryIO

class BaseField(metaclass=abc.ABCMeta):
	def __init__(self, key: bool = False) -> None:
		self.key = key

	@abc.abstractmethod
	def serialize(self, buf: BinaryIO, value) -> None:
		raise NotImplementedError

	@abc.abstractmethod
	def deserialize(self, buf: BinaryIO):
		raise NotImplementedError

class String(BaseField):
	length_struct = struct.Struct('I')

	def serialize(self, buf, value):
		buf.write(self.length_struct.pack(len(value)) + value.encode('utf-8'))

	def deserialize(self, buf) -> str:
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		return buf.read(length).decode('utf-8')

class Boolean(BaseField):
	struct = struct.Struct('?')

	def serialize(self, buf, value: bool):
		buf.write(self.struct.pack(value))

	def deserialize(self, buf) -> bool:
		return self.struct.unpack(buf.read(self.struct.size))[0]

class Integer(BaseField):
	struct = struct.Struct('i')

	def serialize(self, buf, value: int):
		buf.write(self.struct.pack(value))

	def deserialize(self, buf) -> int:
		return self.struct.unpack(buf.read(self.struct.size))[0]

class Array(BaseField):
	length_struct = struct.Struct('I')

	def __init__(self, inner: BaseField, key=False) -> None:
		if not isinstance(inner, BaseField):
			raise Exception('Array inner type is not a field: %r' % (inner))
		self.inner = inner
		super().__init__(key)

	def serialize(self, buf, value: list):
		buf.write(self.length_struct.pack(len(value)))
		for element in value:
			self.inner.serialize(buf, element)

	def deserialize(self, buf) -> list:
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		value = []
		for _ in range(length):
			value.append(self.inner.deserialize(buf))
		return value
