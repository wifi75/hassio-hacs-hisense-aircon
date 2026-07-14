"""Diagnostics support for Hisense Air Conditioner."""

from __future__ import annotations

import enum
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_TO_REDACT = {
    "host", "ip_address", "local_ip", "lanip_key", "lanip_key_id",
    "mac_address", "password", "username",
}


def _native(value: Any) -> Any:
  if isinstance(value, enum.Enum):
    return value.name.lower()
  return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
  """Return privacy-safe diagnostics for a config entry."""
  controller = hass.data[DOMAIN][entry.entry_id]
  devices = []
  for device in controller.devices:
    properties = {
        field: _native(value)
        for field, value in vars(device.get_all_properties()).items()
    }
    devices.append({
        "name": device.name,
        "model": device.model,
        "software_version": device.sw_version,
        "app": device.app,
        "available": device.available,
        "queue_size": device.commands_queue.qsize(),
        "supported_topics": sorted(device.topics),
        "properties": properties,
    })
  return {
      "entry": async_redact_data(dict(entry.data), _TO_REDACT),
      "options": async_redact_data(dict(entry.options), _TO_REDACT),
      "devices": devices,
  }
