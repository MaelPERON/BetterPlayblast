class Software:
	def __init__(self, name: str, simple_icon: str = None):
		self.name = name
		self.simple_icon = f"https://raw.githubusercontent.com/simple-icons/simple-icons/refs/heads/develop/icons/{self.icon_identifier}.svg" if simple_icon else None

	@classmethod
	def icon_identifier(cls, identifier: str):
		name = identifier.split("/")[-1]
		stem = ".".join(name.split(".")[:-1])
		return stem
