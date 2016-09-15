from source import Source

class Publication:

	def __init__(self, title=None, source=None, misc=None):
		self.title = title if title else ""
		self.source = source if source else Source()
		self.misc = misc if misc else ""