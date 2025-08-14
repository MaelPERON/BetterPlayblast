import subprocess
import json
import cv2 as cv
import numpy as np
from PIL import Image
from pathlib import Path
from time import sleep
from metadata import MetadataList, Metadata
from software import SoftwareList as Soft
from overlay import Overlays, OverlayPreview

class Playblast:
	def __init__(self, video_file: Path | str, json_file: Path | str, output_file: Path | str = None, metadatas: list[Metadata] = None, options: dict = {}):
		self.video_file = Path(video_file)
		self.json_file = Path(json_file)
		self.output_file = Path(output_file) if output_file else self.video_file.with_suffix(f".playblast{self.video_file.suffix}")
		self.temp_file = None
		self.data = self._load_json()
		if not self.data:
			raise ValueError(f"JSON file {self.json_file} is empty.")
		
		# Default Values
		## Datas
		icon = getattr(self.data, "icon", Soft.BLENDER.simple_icon)
		self.data["icon"] = icon

		## Metadatas
		if not MetadataList.ICON in metadatas:
			metadatas.append(MetadataList.ICON)

		self.metadatas = metadatas or []
		self.options = options

	def _load_json(self):
		if not self.json_file.exists():
			raise FileNotFoundError(f"JSON file {self.json_file} does not exist.")
		with open(self.json_file) as f:
			try:
				return json.load(f)
			except json.JSONDecodeError as e:
				raise ValueError(f"JSON file {self.json_file} is not valid JSON:\n{e}")

	def render_overlays(self) -> list[Image.Image]:
		overlays = Overlays(self.data, self.metadatas, width=self.width, height=36*2, options=self.options.get("overlay", {}))
		return overlays.bake()

	@classmethod
	def split_overlay(cls, overlay) -> tuple[Image.Image, Image.Image]:
		a,b = np.split(overlay, 2, axis=0)
		a = Image.fromarray(a)
		b = Image.fromarray(b)
		return a,b
	
	def apply_overlays(self, frame: Image.Image, overlay_upper: Image.Image, overlay_lower: Image.Image) -> cv.Mat:
		frame.paste(overlay_upper, (0, 0), overlay_upper)
		frame.paste(overlay_lower, (0, frame.height - overlay_lower.height + 2), overlay_lower)
		return frame
	
	def composite_frame(self, frame: Image.Image, overlay: Image.Image) -> Image.Image:
		overlay = np.array(overlay)

		# Splitting it in two
		overlay_upper, overlay_lower = Playblast.split_overlay(overlay)

		# Alpha compositing over the frame image
		return self.apply_overlays(frame, overlay_upper, overlay_lower)

	def get_source(self) -> cv.VideoCapture: return cv.VideoCapture(str(self.video_file))

	def update_capture_properties(self, source: cv.VideoCapture):
		self.frame_count = int(source.get(cv.CAP_PROP_FRAME_COUNT))
		self.width = int(source.get(cv.CAP_PROP_FRAME_WIDTH))
		self.height = int(source.get(cv.CAP_PROP_FRAME_HEIGHT))
		self.fps = int(source.get(cv.CAP_PROP_FPS))

	def has_audio(self) -> bool:
		probe_cmd = [
			"ffprobe",
			"-v", "error",
			"-select_streams", "a",
			"-show_entries", "stream=codec_type",
			"-of", "json",
			str(self.video_file)
		]
		probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
		try:
			info = json.loads(probe_result.stdout)
			return any(stream.get("codec_type") == "audio" for stream in info.get("streams", []))
		except Exception:
			return False

	def preview(self, frame: int = 0):
		source = self.get_source()
		self.update_capture_properties(source)

		if frame < 0 or frame >= self.frame_count:
			raise ValueError(f"Frame index {frame} is out of bounds. Must be between 0 and {self.frame_count - 1}.")

		frame_head = 0
		while source.isOpened():
			ret, matlike = source.read()
			frame_head += 1
			frame_index = frame_head - 1
			if not ret:
				break

			if not frame_index == frame:
				continue

			frame_image = Image.fromarray(cv.cvtColor(matlike, cv.COLOR_BGR2RGB))
			overlay = OverlayPreview(self.data, self.metadatas, frame_index, self.width, 36*2, self.options)
			overlay_image = overlay.bake()
			composite = self.composite_frame(frame_image, overlay_image)
			composite.show()
			sleep(0.5)
			break

		source.release()

	def render(self, preview: bool = False):
		source = self.get_source()
		self.update_capture_properties(source)

		# Create a temporary file for video without audio
		self.temp_file = self.output_file.with_suffix(".temp.mp4")
		out = cv.VideoWriter(str(self.temp_file), cv.VideoWriter.fourcc(*"mp4v"), self.fps, (self.width, self.height))

		overlays : list[Image.Image] = self.render_overlays()

		frame_head = 0
		while source.isOpened():
			ret, matlike = source.read()
			frame_head += 1
			frame_index = frame_head - 1
			if not ret:
				break

			frame_image = Image.fromarray(cv.cvtColor(matlike, cv.COLOR_BGR2RGB))

			# Loading the overlay as an array
			overlay : Image.Image = overlays[frame_index]
			if not overlay:
				continue

			composite = self.composite_frame(frame_image, overlay)
			composite = cv.cvtColor(np.array(composite), cv.COLOR_RGB2BGR)

			# Displaying the result
			if preview:
				scale = int(1 / 0.5)
				scaled = cv.resize(composite, (composite.shape[1] // scale, composite.shape[0] // scale))
				cv.imshow("Playblast", scaled)
				if cv.waitKey(1) & 0xFF == ord('q'):
					break

			out.write(composite)

		cv.destroyAllWindows()
		source.release()
		out.release()

		# Combine audio from original video with processed video using ffmpeg (if necessary)
		if self.has_audio():
			cmd = [
				"ffmpeg",
				"-y",
				"-i", str(self.temp_file),
				"-i", str(self.video_file),
				"-c:v", "copy",
				"-c:a", "aac",
				"-map", "0:v:0",
				"-map", "1:a:0",
				str(self.output_file)
			]
			subprocess.run(cmd, check=True)
			self.temp_file.unlink(missing_ok=True)
		else:
			if self.output_file.exists():
				try:
					self.output_file.unlink(missing_ok=True)
				except PermissionError as e:
					print(f"Error deleting output file: {e}")
			self.temp_file.rename(self.output_file)
		self.temp_file = None