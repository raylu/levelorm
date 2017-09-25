import contextlib
import unittest

class BaseTest(unittest.TestCase):
	@contextlib.contextmanager
	def assert_raises(self, exc_type):
		try:
			yield
		except Exception as e:
			if not isinstance(e, exc_type):
				raise
		else:
			self.fail('expected %s' % exc_type.__name__)
