from pathlib import Path
import yaml

def load_config() -> dict:
	with open(Path(__file__) / "../config.yaml", 'r') as file:
		config = yaml.safe_load(file)
	return config

CONFIG = load_config()