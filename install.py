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

def missing_modules() -> list[str]:
	installed_modules = list_installed_modules()
	return [pkg for pkg in PACKAGES.values() if pkg not in installed_modules]

def missing_packages() -> list[str]:
	installed_modules = list_installed_modules()
	return [key for key, value in PACKAGES.items() if value not in installed_modules]

