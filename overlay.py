import asyncio
from pyppeteer import browser, launch

class Overlays:
	def __init__(self, frame_count, data, metadatas, pool_size: int = 20):
		self.frame_count = frame_count
		self.data = data
		self.metadatas = metadatas
		self.pool_size = pool_size
		self.images = [None] * self.frame_count

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

	