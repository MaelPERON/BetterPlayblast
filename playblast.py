import json
from pathlib import Path
from metadata import MetadataList as Metadata

class Playblast:
	def __init__(self, video_file: Path | str, json_file: Path | str, metadatas: list[Metadata] = None):
		self.video_file = Path(video_file)
		self.json_file = Path(json_file)
		self.data = self._load_json()
		if not self.data:
			raise ValueError(f"JSON file {self.json_file} is empty.")

		self.metadatas = metadatas or []

	def _load_json(self):
		if not self.json_file.exists():
			raise FileNotFoundError(f"JSON file {self.json_file} does not exist.")
		with open(self.json_file) as f:
			try:
				return json.load(f)
			except json.JSONDecodeError as e:
				raise ValueError(f"JSON file {self.json_file} is not valid JSON:\n{e}")