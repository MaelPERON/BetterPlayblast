from pathlib import Path
import json

class Playblast:
	def __init__(self, video_file: Path | str, json_file: Path | str):
		self.video_file = Path(video_file)
		self.json_file = Path(json_file)
		self.data = self._load_json()

	def _load_json(self):
		if not self.json_file.exists():
			return {}
		with open(self.json_file) as f:
			return json.load(f)