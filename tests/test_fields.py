import io
import struct

from levelorm import fields
from levelorm.orm import InvalidModel
from .base import BaseTest

class TestFields(BaseTest):
	def test_invalid(self):
		with self.assert_raises(InvalidModel):
			fields.Array(fields.String)

	def test_invalid_value(self):
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

		float_field = fields.Float()
		with self.assert_raises(struct.error):
			float_field.serialize(buf, '1.0')

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

	def test_range(self):
		buf = io.BytesIO()
		f = 2**128 + 1.0 # the maximum representable binary32 is about 2**128
		float_field = fields.Float()
		float_field.serialize(buf, f)
		buf.seek(0)
		assert float_field.deserialize(buf) == f
