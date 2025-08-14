import importlib
PACKAGES = {
	"pillow": "PIL",
	"opencv-python": "cv2",
	"numpy": "numpy",
	"PyYAML": "yaml",
	"pyppeteer": "pyppeteer"
}

def list_installed_modules() -> list[str]:
	installed_modules = []
	for package in PACKAGES.values():
		try:
			importlib.import_module(package)
			installed_modules.append(package)
		except ImportError:
			pass
	return installed_modules
