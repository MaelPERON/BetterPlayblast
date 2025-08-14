import os
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1230501'
import asyncio
from pyppeteer import browser, launch
from PIL import Image
from io import BytesIO

from metadata import MetadataList, Metadata
from config import CONFIG

PYPPETEER_OPTIONS = {
	'headless': True,
	'args': ['--no-sandbox', '--disable-setuid-sandbox']
}

class Overlays:
	def __init__(self, data, metadatas: list[Metadata], width: int = 1920, height: int = 36*2, pool_size: int = 20, software: str = "blender", options: dict = {}):
		self.data = data
		self.metadatas = metadatas
		self.frame_count = len(data.get('frames', []))
		self.frame_start = self.data.get('frame_start', 1)
		self.frame_end = self.data.get('frame_end', self.frame_count)
		self.width = width
		self.height = height
		self.options = options
		print(self.options)
		self.pool_size = pool_size
		self.semaphore = asyncio.Semaphore(self.pool_size/2)
		self.images = [None] * self.frame_count
		with open("overlay.html", encoding="utf-8") as f:
			self.template = f.read()
			f.close()

	def bake(self):
		asyncio.run(self._bake())
		return self.images

	async def _bake(self):
		PYPPETEER_OPTIONS["defaultViewport"] = {
			'width': self.width,
			'height': self.height
		}
		self.browser = await launch(options=PYPPETEER_OPTIONS)

		self.pages = [await self.browser.newPage() for _ in range(self.pool_size)]

		tasks = [self.call_bake_overlay(i) for i in range(self.frame_count)]
		await asyncio.gather(*tasks)

		for page in self.pages:
			await page.close()

		await self.browser.close()

	async def call_bake_overlay(self, index):
		async with self.semaphore:
			content = self.parse_template(index)
			img = await self.bake_overlay(self.pages[index % self.pool_size], content, index)
			self.images[index] = img
			return

	async def bake_overlay(self, page, content, index, save_folder: str = None):
		await page.setContent(content)

		# Wait until all resources (images, stylesheets, scripts, etc.) are loaded, including SVG images
		await page.evaluate("""
			async () => {
				if (document.readyState !== 'complete') {
					await new Promise(resolve => {
						window.addEventListener('load', resolve, { once: true });
					});
				}
				// Wait for all <img> elements to be fully loaded
				const images = Array.from(document.images);
				await Promise.all(images.map(img => {
					if (img.complete) return Promise.resolve();
					return new Promise(resolve => {
						img.addEventListener('load', resolve, { once: true });
						img.addEventListener('error', resolve, { once: true });
					});
				}));
			}
		""")
		# Take screenshot as PNG bytes in memory, ensure PNG format
		png_bytes = await page.screenshot({'omitBackground': True, 'type': 'png'})

		# Load image from bytes using Pillow
		img = Image.open(BytesIO(png_bytes))
		if img.mode != 'RGBA':
			img = img.convert('RGBA')  # Ensure transparency is preserved
		if save_folder:
			os.makedirs(save_folder, exist_ok=True)
			path = os.path.join(save_folder, f"frame_{(index+1):04d}.png")
			img.save(path)
		return img

	def parse_template(self, index):
		content = self.template
		ids = []
		for metadata in self.metadatas:
			source = self.data
			if metadata.frame_dependant:
				frames = self.data.get("frames", [])
				if not frames or index >= len(frames):
					continue
				source = frames[index]

			key = metadata.key
			value = source.get(key, None)
			if value: ids.append(key)
			if isinstance(value, float): value = f"{value:.2f}"
			content = content.replace(f"{{{{{key}}}}}", str(value))

		frame_maps = {
			"global_frame_curr": index+1,
			"global_frame_in": 1,
			"global_frame_out": self.frame_count,
			"local_frame_curr": self.frame_start + index,
			"local_frame_in": self.frame_start,
			"local_frame_out": self.frame_end
		}

		for key, value in frame_maps.items():
			content = content.replace(f"{{{{{key}}}}}", str(value).zfill(4))

		# Filter metadatas elements IDs
		content = content.replace("//{SELECTED_IDS}", f"SELECTED_IDS = {ids}")

		# Displaying icons or span
		show_icons = self.options.get('show_icons', CONFIG.get('overlay_show_icons'))
		content = content.replace("//{SHOW_ICONS}", f"show_icons = {str(show_icons).lower()}")

		# Custom Icon
		if (custom_logo := self.options.get("custom_logo", None)):
			content = content.replace("//{CUSTOM_LOGO}", f"custom_logo = '{custom_logo}'")

		# Disable Logo Filter
		if (disable := self.options.get("disable_logo_filter", False)):
			content = content.replace("//{DISABLE_LOGO_FILTER}", f"disable_logo_filter = {str(disable).lower()}")

		if (scale := self.options.get("logo_size", None)):
			content = content.replace("//{LOGO_SIZE}", f"logo_size = '{scale}'")

		if (note_color := self.options.get("note_color", None)):
			content = content.replace("//{NOTE_COLOR}", f"note_color = '{note_color}'")

		return content