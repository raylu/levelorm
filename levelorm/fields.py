import abc
import struct

class BaseField(metaclass=abc.ABCMeta):
	def __init__(self, key=False):
		self.key = key

	@abc.abstractmethod
	def serialize(self, buf, value):
		raise NotImplementedError

	@abc.abstractmethod
	def deserialize(self, buf):
		raise NotImplementedError

class String(BaseField):
	length_struct = struct.Struct('I')

	def serialize(self, buf, value):
		buf.write(self.length_struct.pack(len(value)) + value.encode('utf-8'))

	def deserialize(self, buf):
		length = self.length_struct.unpack(buf.read(self.length_struct.size))[0]
		return buf.read(length).decode('utf-8')

class Boolean(BaseField):
	struct = struct.Struct('?')

	def serialize(self, buf, value):
		buf.write(self.struct.pack(value))

	def deserialize(self, buf):
		return self.struct.unpack(buf.read(self.struct.size))[0]
