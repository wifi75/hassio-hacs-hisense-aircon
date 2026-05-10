"""Config flow for Hisense Air Conditioner."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .app_mappings import SECRET_MAP
from .const import (
    CONF_APP,
    CONF_CALLBACK_PORT,
    CONF_DEVICE_NAME,
    CONF_DEVICES,
    CONF_LANIP_KEY,
    CONF_LANIP_KEY_ID,
    CONF_LOCAL_IP,
    CONF_MAC_ADDRESS,
    CONF_MODEL,
    CONF_SETUP_METHOD,
    CONF_STATUS_INTERVAL,
    CONF_SW_VERSION,
    CONF_TEMP_TYPE,
    DEFAULT_CALLBACK_PORT,
    DEFAULT_STATUS_INTERVAL,
    DOMAIN,
    SETUP_METHOD_CLOUD,
    SETUP_METHOD_MANUAL,
)
from .discovery import perform_discovery

_LOGGER = logging.getLogger(__name__)

_ADVANCED_SETTINGS = "advanced_settings"


class HisenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for Hisense Air Conditioner."""

  VERSION = 1

  @staticmethod
  @callback
  def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> HisenseOptionsFlow:
    """Return the options flow."""
    return HisenseOptionsFlow(config_entry)

  async def async_step_user(self, user_input: dict[str, Any] | None = None):
    """Choose setup method."""
    if user_input is not None:
      if user_input[CONF_SETUP_METHOD] == SETUP_METHOD_MANUAL:
        return await self.async_step_manual()
      return await self.async_step_cloud()

    return self.async_show_form(
        step_id="user",
        data_schema=vol.Schema({
            vol.Required(CONF_SETUP_METHOD, default=SETUP_METHOD_CLOUD):
                SelectSelector(
                    SelectSelectorConfig(
                        options=[SETUP_METHOD_CLOUD, SETUP_METHOD_MANUAL],
                        mode=SelectSelectorMode.DROPDOWN,
                    ))
        }),
    )

  async def async_step_cloud(self, user_input: dict[str, Any] | None = None):
    """Discover devices through the Hisense/Ayla account."""
    errors: dict[str, str] = {}
    if user_input is not None:
      advanced_settings = user_input.get(_ADVANCED_SETTINGS, {})
      try:
        session = async_get_clientsession(self.hass)
        discovered = await perform_discovery(
            session,
            user_input[CONF_APP],
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            _blank_to_none(advanced_settings.get(CONF_DEVICE_NAME)),
            False,
        )
      except Exception:
        _LOGGER.exception("Hisense cloud discovery failed")
        errors["base"] = "cannot_connect"
      else:
        if not discovered:
          errors["base"] = "device_not_found"
        else:
          devices = [_device_config_from_cloud(user_input[CONF_APP], device) for device in discovered]
          await self.async_set_unique_id(_unique_id(devices))
          self._abort_if_unique_id_configured()
          title = ", ".join(device["name"] for device in devices)
          return self.async_create_entry(
              title=title,
              data={
                  CONF_APP: user_input[CONF_APP],
                  CONF_DEVICES: devices,
                  CONF_LOCAL_IP: _blank_to_none(advanced_settings.get(CONF_LOCAL_IP)),
                  CONF_CALLBACK_PORT: advanced_settings.get(CONF_CALLBACK_PORT,
                                                            DEFAULT_CALLBACK_PORT),
                  CONF_STATUS_INTERVAL: advanced_settings.get(CONF_STATUS_INTERVAL,
                                                              DEFAULT_STATUS_INTERVAL),
              },
          )

    return self.async_show_form(
        step_id="cloud",
        data_schema=vol.Schema({
            vol.Required(CONF_APP, default="hisense-eu"):
                SelectSelector(
                    SelectSelectorConfig(
                        options=sorted(SECRET_MAP),
                        mode=SelectSelectorMode.DROPDOWN,
                    )),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD):
                TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional(_ADVANCED_SETTINGS, default={}):
                section(
                    vol.Schema({
                        vol.Optional(CONF_DEVICE_NAME, default=""): str,
                        vol.Optional(CONF_LOCAL_IP, default=""): str,
                        vol.Required(CONF_CALLBACK_PORT, default=DEFAULT_CALLBACK_PORT): int,
                        vol.Required(CONF_STATUS_INTERVAL, default=DEFAULT_STATUS_INTERVAL): int,
                    }),
                    {"collapsed": True},
                ),
        }),
        errors=errors,
    )

  async def async_step_manual(self, user_input: dict[str, Any] | None = None):
    """Set up a device from an existing LAN key."""
    errors: dict[str, str] = {}
    if user_input is not None:
      try:
        device = _device_config_from_manual(user_input)
      except (KeyError, ValueError):
        errors["base"] = "invalid_manual_config"
      else:
        await self.async_set_unique_id(_unique_id([device]))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=device["name"],
            data={
                CONF_APP: device["app"],
                CONF_DEVICES: [device],
                CONF_LOCAL_IP: _blank_to_none(user_input.get(CONF_LOCAL_IP)),
                CONF_CALLBACK_PORT: user_input[CONF_CALLBACK_PORT],
                CONF_STATUS_INTERVAL: user_input[CONF_STATUS_INTERVAL],
            },
        )

    return self.async_show_form(
        step_id="manual",
        data_schema=vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_APP, default="hisense-eu"):
                SelectSelector(
                    SelectSelectorConfig(
                        options=sorted(SECRET_MAP),
                        mode=SelectSelectorMode.DROPDOWN,
                    )),
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_MAC_ADDRESS): str,
            vol.Required(CONF_LANIP_KEY): str,
            vol.Required(CONF_LANIP_KEY_ID): int,
            vol.Required(CONF_MODEL, default="AEH-W4E1"): str,
            vol.Optional(CONF_SW_VERSION, default=""): str,
            vol.Required(CONF_TEMP_TYPE, default="C"): vol.In(["C", "F"]),
            vol.Optional(CONF_LOCAL_IP, default=""): str,
            vol.Required(CONF_CALLBACK_PORT, default=DEFAULT_CALLBACK_PORT): int,
            vol.Required(CONF_STATUS_INTERVAL, default=DEFAULT_STATUS_INTERVAL): int,
        }),
        errors=errors,
    )


class HisenseOptionsFlow(config_entries.OptionsFlow):
  """Handle Hisense options."""

  def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
    self._entry = config_entry

  async def async_step_init(self, user_input: dict[str, Any] | None = None):
    """Manage runtime options."""
    if user_input is not None:
      return self.async_create_entry(
          title="",
          data={
              CONF_LOCAL_IP: _blank_to_none(user_input.get(CONF_LOCAL_IP)),
              CONF_CALLBACK_PORT: user_input[CONF_CALLBACK_PORT],
              CONF_STATUS_INTERVAL: user_input[CONF_STATUS_INTERVAL],
          },
      )

    return self.async_show_form(
        step_id="init",
        data_schema=vol.Schema({
            vol.Optional(
                CONF_LOCAL_IP,
                default=self._entry.options.get(
                    CONF_LOCAL_IP,
                    self._entry.data.get(CONF_LOCAL_IP) or "",
                ),
            ):
                str,
            vol.Required(
                CONF_CALLBACK_PORT,
                default=self._entry.options.get(
                    CONF_CALLBACK_PORT,
                    self._entry.data.get(CONF_CALLBACK_PORT, DEFAULT_CALLBACK_PORT),
                ),
            ):
                int,
            vol.Required(
                CONF_STATUS_INTERVAL,
                default=self._entry.options.get(
                    CONF_STATUS_INTERVAL,
                    self._entry.data.get(CONF_STATUS_INTERVAL, DEFAULT_STATUS_INTERVAL),
                ),
            ):
                int,
        }),
    )


def _blank_to_none(value: str | None) -> str | None:
  if value is None:
    return None
  value = value.strip()
  return value or None


def _normalize_mac(mac_address: str) -> str:
  return mac_address.replace(":", "").replace("-", "").lower()


def _device_config_from_cloud(app: str, device: dict[str, Any]) -> dict[str, Any]:
  return {
      "name": device["product_name"],
      "app": app,
      "model": device.get("oem_model") or device.get("model") or "unknown",
      "sw_version": device.get("sw_version") or "",
      "dsn": device.get("dsn"),
      "temp_type": device.get("temp_type") or "F",
      "mac_address": _normalize_mac(device["mac"]),
      "ip_address": device["lan_ip"],
      "lanip_key": device["lanip_key"],
      "lanip_key_id": device["lanip_key_id"],
  }


def _device_config_from_manual(user_input: dict[str, Any]) -> dict[str, Any]:
  return {
      "name": user_input[CONF_NAME],
      "app": user_input[CONF_APP],
      "model": user_input[CONF_MODEL],
      "sw_version": user_input.get(CONF_SW_VERSION) or "",
      "dsn": None,
      "temp_type": user_input[CONF_TEMP_TYPE],
      "mac_address": _normalize_mac(user_input[CONF_MAC_ADDRESS]),
      "ip_address": user_input[CONF_HOST],
      "lanip_key": user_input[CONF_LANIP_KEY],
      "lanip_key_id": user_input[CONF_LANIP_KEY_ID],
  }


def _unique_id(devices: list[dict[str, Any]]) -> str:
  return ",".join(sorted(device["mac_address"] for device in devices))
