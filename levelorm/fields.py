class BaseField:
	formatstr = None

	def __init__(self, key=False):
		self.key = key

class String(BaseField):
	pass

class Boolean(BaseField):
	formatstr = '?'
