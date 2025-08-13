import json
from pathlib import Path
from metadata import MetadataList, Metadata

class Playblast:
	def __init__(self, video_file: Path | str, json_file: Path | str, output_file: Path | str = None, metadatas: list[Metadata] = None):
		self.video_file = Path(video_file)
		self.json_file = Path(json_file)
		self.output_file = Path(output_file) if output_file else self.video_file.parent() / (self.video_file.stem + "_rendered" + self.video_file.suffix)
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