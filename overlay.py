import asyncio
from pyppeteer import browser, launch

class Overlays:
	def __init__(self, frame_count, data, metadatas, pool_size: int = 20):
		self.frame_count = frame_count
		self.data = data
		self.metadatas = metadatas
		self.pool_size = pool_size
		self.images = [None] * self.frame_count

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

		semaphore = asyncio.Semaphore(self.pool_size/2)

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
