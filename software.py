class Software:
	def __init__(self, name: str, simple_icon: str = None):
		self.name = name

	@classmethod
	def icon_identifier(cls, identifier: str):
		name = identifier.split("/")[-1]
		stem = ".".join(name.split(".")[:-1])
		return stem
