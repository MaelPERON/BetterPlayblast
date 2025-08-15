import importlib
PACKAGES = {
	"pillow": "PIL",
	"opencv-python": "cv2",
	"numpy": "numpy",
	"PyYAML": "yaml",
	"pyppeteer": "pyppeteer"
}

cached_modules = []

def list_installed_modules(refresh: bool = True, save_cache: bool = True) -> list[str]:
	global cached_modules
	if not refresh and cached_modules:
		return cached_modules

	installed_modules = []
	for package in PACKAGES.values():
		try:
			importlib.import_module(package)
			installed_modules.append(package)
		except ImportError:
			pass

	if save_cache: cached_modules = installed_modules
	return installed_modules

def missing_modules(refresh: bool = True, save_cache: bool = True) -> list[str]:
	installed_modules = list_installed_modules(refresh=refresh, save_cache=save_cache)
	return [pkg for pkg in PACKAGES.values() if pkg not in installed_modules]

def missing_packages(refresh: bool = True, save_cache: bool = True) -> list[str]:
	installed_modules = list_installed_modules(refresh=refresh, save_cache=save_cache)
	return [key for key, value in PACKAGES.items() if value not in installed_modules]

def all_installed(refresh: bool = True, save_cache: bool = True) -> bool:
	installed_modules = list_installed_modules(refresh=refresh, save_cache=save_cache)
	return len(installed_modules) == len(PACKAGES)