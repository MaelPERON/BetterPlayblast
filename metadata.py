from software import Software
from software import SoftwareList as Soft

class Metadata:
	def __init__(self, key, frame_dependant: bool = False, software: Software = None):
		self.key = key
		self.frame_dependant = frame_dependant
		self.software = software

class MetadataList:
	FILE = Metadata("filename")
	FRAME_RANGE = Metadata("frame_range")
	SCENE = Metadata("scene", software=Soft.BLENDER)
	MEMORY = Metadata("memory", frame_dependant=True)
	RENDER_TIME = Metadata("render_time", frame_dependant=True)
	RESOLUTION = Metadata("resolution")
	CAMERA = Metadata("camera", frame_dependant=True)
	LENS = Metadata("lens", frame_dependant=True)
	MARKER = Metadata("marker", frame_dependant=True)
	STRIP = Metadata("sequencer_strip", software=Soft.BLENDER, frame_dependant=True)
	COMMENT = Metadata("comment")
	USER = Metadata("user")
	HOSTNAME = Metadata("hostname")
	DATE = Metadata("date")