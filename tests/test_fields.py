import contextlib
import io
import struct
import unittest

from levelorm import fields

class TestFields(unittest.TestCase):
	def test_invalid(self):
		buf = io.BytesIO()

		str_field = fields.String()
		with self.assert_raises(AttributeError):
			str_field.serialize(buf, b'hi')

		blob_field = fields.Blob()
		with self.assert_raises(TypeError):
			blob_field.serialize(buf, 'hi')

		bool_field = fields.Boolean()
		with self.assert_raises(TypeError):
			bool_field.serialize(buf, 2)

		int_field = fields.Integer()
		with self.assert_raises(struct.error):
			int_field.serialize(buf, '0')

		array_field = fields.Array(fields.String())
		with self.assert_raises(TypeError):
			array_field.serialize(buf, 'hi')

	def test_overflow(self):
		buf = io.BytesIO()

		int_field = fields.Integer()
		with self.assert_raises(struct.error):
			int_field.serialize(buf, 2**31 + 1)

		str_field = fields.String()
		class LongStr:
			def encode(self, encoding):
				return self
			def __len__(self):
				return 2**32 + 1
		with self.assert_raises(struct.error):
			str_field.serialize(buf, LongStr())

		blob_field = fields.Blob()
		class LongBytes:
			def __len__(self):
				return 2**32 + 1
		with self.assert_raises(struct.error):
			blob_field.serialize(buf, LongBytes())

	@contextlib.contextmanager
	def assert_raises(self, exc_type):
		try:
			yield
		except Exception as e:
			if not isinstance(e, exc_type):
				raise
		else:
			self.fail('expected %s' % exc_type.__name__)
