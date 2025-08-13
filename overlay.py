import os
os.environ['PYPPETEER_CHROMIUM_REVISION'] = '1230501'
import asyncio
from pyppeteer import browser, launch
from PIL import Image
from io import BytesIO

class Overlays:
	def __init__(self, data, metadatas, pool_size: int = 20):
		self.data = data
		self.metadatas = metadatas
		self.frame_count = len(data.get('frames', []))
		self.frame_start = self.data.get('frame_start', 1)
		self.frame_end = self.data.get('frame_end', self.frame_count)
		self.pool_size = pool_size
		self.semaphore = asyncio.Semaphore(self.pool_size/2)
		self.images = [None] * self.frame_count
		with open("overlay.html", encoding="utf-8") as f:
			self.template = f.read()
			f.close()

		asyncio.run(self.bake())

	async def bake(self):
		self.browser = await launch(options={
			'headless': True,
			'args': ['--no-sandbox', '--disable-setuid-sandbox'],
			'defaultViewport': {
				'width': 1920,
				'height': 36*2
			}
		})

		self.pages = [await self.browser.newPage() for _ in range(self.pool_size)]

		# ...

		for page in self.pages:
			await page.close()

		await self.browser.close()

	async def bake_overlay(self, page, content):
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
			ids.append(key)
			value = source.get(key, None)
			if value is not None:
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
			content = content.replace(f"{{{{{key}}}}}", str(value))

		content = content.replace("//{SELECTED_IDS}", f"SELECTED_IDS = {ids}")
		return content