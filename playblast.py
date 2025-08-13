import json
import cv2 as cv
from pathlib import Path
from metadata import MetadataList, Metadata

class Playblast:
	def __init__(self, video_file: Path | str, json_file: Path | str, output_file: Path | str = None, metadatas: list[Metadata] = None):
		self.video_file = Path(video_file)
		self.json_file = Path(json_file)
		self.output_file = Path(output_file) if output_file else self.video_file.with_suffix(f".playblast{self.video_file.suffix}")
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
			
	def render(self):
		source = cv.VideoCapture(str(self.video_file))
		frame_count = int(source.get(cv.CAP_PROP_FRAME_COUNT))
		self.width = int(source.get(cv.CAP_PROP_FRAME_WIDTH))
		self.height = int(source.get(cv.CAP_PROP_FRAME_HEIGHT))
		self.fps = int(source.get(cv.CAP_PROP_FPS))

		# Create a temporary file for video without audio
		temp_video_file = self.output_file.with_suffix(".temp.mp4")
		out = cv.VideoWriter(str(temp_video_file), cv.VideoWriter.fourcc(*"mp4v"), self.fps, (self.width, self.height))

		overlays : list[Image.Image] = self.render_overlays(frame_count)

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
			overlay = np.array(overlay)

			# Splitting it in two
			overlay_upper, overlay_lower = np.split(overlay, 2, axis=0)
			overlay_lower = Image.fromarray(overlay_lower)
			overlay_upper = Image.fromarray(overlay_upper)

			# Alpha compositing over the frame image
			frame_image.paste(overlay_upper, (0, 0), overlay_upper)
			frame_image.paste(overlay_lower, (0, self.height - overlay_lower.height + 2), overlay_lower)
			composite = cv.cvtColor(np.array(frame_image), cv.COLOR_RGB2BGR)

			# Displaying the result
			scale = int(1 / 0.5)
			scaled = cv.resize(composite, (composite.shape[1] // scale, composite.shape[0] // scale))
			cv.imshow("Playblast", scaled)
			if cv.waitKey(1) & 0xFF == ord('q'):
				break

			out.write(composite)

		cv.destroyAllWindows()
		source.release()
		out.release()

		# Combine audio from original video with processed video using ffmpeg
		cmd = [
			"ffmpeg",
			"-y",
			"-i", str(temp_video_file),
			"-i", str(self.video_file),
			"-c:v", "copy",
			"-c:a", "aac",
			"-map", "0:v:0",
			"-map", "1:a:0",
			str(self.output_file)
		]
		subprocess.run(cmd, check=True)

		# Remove temporary video file
		temp_video_file.unlink(missing_ok=True)