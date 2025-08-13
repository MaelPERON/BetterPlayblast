class Software:
	def __init__(self, name: str, simple_icon: str = None):
		self.name = name
		self.simple_icon = f"https://raw.githubusercontent.com/simple-icons/simple-icons/refs/heads/develop/icons/{simple_icon}.svg" if simple_icon else None

class SoftwareList:
	BLENDER = Software("blender", simple_icon="blender")
	AUTODESK_MAYA = Software("autodesk_maya", simple_icon="autodeskmaya")
	HOUDINI = Software("houdini", simple_icon="houdini")