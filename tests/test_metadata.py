import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]


def _load_properties():
  path = ROOT / "custom_components/hisense_aircon/properties.py"
  spec = importlib.util.spec_from_file_location("hisense_properties", path)
  module = importlib.util.module_from_spec(spec)
  sys.modules[spec.name] = module
  spec.loader.exec_module(module)
  return module


def _keys(value, prefix=""):
  result = set()
  if isinstance(value, dict):
    for key, child in value.items():
      path = f"{prefix}.{key}" if prefix else key
      result.add(path)
      result.update(_keys(child, path))
  return result


def test_unknown_indoor_temperature_at_startup():
  assert _load_properties().AcProperties().f_temp_in is None


def test_translation_files_have_matching_keys():
  translations = ROOT / "custom_components/hisense_aircon/translations"
  english = json.loads((translations / "en.json").read_text(encoding="utf-8"))
  italian = json.loads((translations / "it.json").read_text(encoding="utf-8"))
  assert _keys(english) == _keys(italian)


def test_manifest_version_matches_changelog():
  manifest = json.loads((ROOT / "custom_components/hisense_aircon/manifest.json").read_text())
  changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
  assert f"## {manifest['version']}" in changelog
