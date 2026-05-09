"""Shared entity helpers for Hisense Air Conditioner."""

from __future__ import annotations

from dataclasses import Field, fields
import enum
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .aircon import Device
from .const import DOMAIN, signal_device_update
from .controller import HisenseController


class HisenseEntity(Entity):
  """Base entity for a Hisense device property."""

  _attr_has_entity_name = True

  def __init__(self, controller: HisenseController, device: Device) -> None:
    self.controller = controller
    self.device = device
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, device.mac_address)},
        manufacturer=f"Hisense ({device.app})",
        model=device.model,
        name=device.name,
        sw_version=device.sw_version,
    )

  @property
  def available(self) -> bool:
    """Return if entity is available."""
    return self.device.available

  async def async_added_to_hass(self) -> None:
    """Subscribe to device updates."""
    self.async_on_remove(
        async_dispatcher_connect(
            self.hass,
            signal_device_update(self.controller.entry.entry_id, self.device.mac_address),
            self._handle_device_update,
        ))

  def _handle_device_update(self, prop_name: str, value: Any) -> None:
    self.async_write_ha_state()


class HisensePropertyEntity(HisenseEntity):
  """Base entity for a single device property."""

  def __init__(self, controller: HisenseController, device: Device, field: Field[Any]) -> None:
    super().__init__(controller, device)
    self.field = field
    self.prop_name = field.name
    self._attr_name = _friendly_name(field.name)
    self._attr_unique_id = f"{device.mac_address}_{field.name}"

  @property
  def native_value(self) -> Any:
    """Return the current property value."""
    return property_to_native_value(self.device.get_property(self.prop_name))

  def _handle_device_update(self, prop_name: str, value: Any) -> None:
    if prop_name in (self.prop_name, "available"):
      self.async_write_ha_state()


def property_fields(device: Device) -> list[Field[Any]]:
  """Return dataclass fields for a device."""
  return list(fields(device.get_all_properties()))


def property_to_native_value(value: Any) -> Any:
  """Convert protocol values to HA-friendly values."""
  if isinstance(value, enum.Enum):
    return value.name.lower()
  return value


def is_enum_type(value_type: type[Any]) -> bool:
  """Return if a dataclass field type is an enum."""
  return isinstance(value_type, type) and issubclass(value_type, enum.Enum)


def enum_options(value_type: type[enum.Enum]) -> list[str]:
  """Return lower-case enum options."""
  return [option.name.lower() for option in value_type]


def is_binary_enum(value_type: type[enum.Enum]) -> bool:
  """Return if enum is an ON/OFF style switch."""
  return {option.name for option in value_type} == {"OFF", "ON"}


def _friendly_name(prop_name: str) -> str:
  return prop_name.replace("_", " ").title()
