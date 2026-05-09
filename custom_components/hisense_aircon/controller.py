"""Runtime controller for Hisense LAN devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .aircon import Device
from .const import (
    ACTIVE_CONTROLLER,
    CONF_CALLBACK_PORT,
    CONF_DEVICES,
    CONF_LOCAL_IP,
    CONF_STATUS_INTERVAL,
    DEFAULT_CALLBACK_PORT,
    DEFAULT_STATUS_INTERVAL,
    DOMAIN,
    VIEWS_REGISTERED,
    signal_device_update,
)
from .notifier import Notifier
from .query_handlers import QueryHandlers

_LOGGER = logging.getLogger(__name__)

_WAIT_FOR_EMPTY_QUEUE = 10.0


class HisenseController:
  """Own the LAN server endpoints, notifier and device update loops."""

  def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
    self.hass = hass
    self.entry = entry
    self.devices = [
        Device.create(device_config, self._notify_device)
        for device_config in entry.data[CONF_DEVICES]
    ]
    self.devices_by_mac = {device.mac_address: device for device in self.devices}
    self.handlers = QueryHandlers(self.devices)
    self._tasks: list[asyncio.Task[Any]] = []
    self._notifier = Notifier(
        self._option(CONF_CALLBACK_PORT, DEFAULT_CALLBACK_PORT),
        self._option(CONF_LOCAL_IP),
        loop=hass.loop,
    )

  def _option(self, key: str, default: Any | None = None) -> Any:
    return self.entry.options.get(key, self.entry.data.get(key, default))

  async def async_start(self) -> None:
    """Start the LAN bridge."""
    self._register_views()

    for device in self.devices:
      self._notifier.register_device(device)
      device.add_property_change_listener(self._handle_property_update)

    session = async_get_clientsession(self.hass)
    self._tasks.append(self.hass.async_create_task(self._notifier.start(session)))
    for device in self.devices:
      self._tasks.append(self.hass.async_create_task(self._query_status_device(device)))

  async def async_stop(self) -> None:
    """Stop background work."""
    await self._notifier.stop()
    for device in self.devices:
      device.remove_property_change_listener(self._handle_property_update)
    for task in self._tasks:
      task.cancel()
    if self._tasks:
      await asyncio.gather(*self._tasks, return_exceptions=True)
    self._tasks.clear()

  def get_device(self, mac_address: str) -> Device | None:
    """Return a device by MAC address."""
    return self.devices_by_mac.get(mac_address)

  def _notify_device(self) -> None:
    self._notifier.notify()

  def _handle_property_update(
      self,
      mac_address: str,
      prop_name: str,
      value: Any,
      retain: bool = False,
  ) -> None:
    async_dispatcher_send(
        self.hass,
        signal_device_update(self.entry.entry_id, mac_address),
        prop_name,
        value,
    )

  async def _query_status_device(self, device: Device) -> None:
    status_interval = self._option(CONF_STATUS_INTERVAL, DEFAULT_STATUS_INTERVAL)
    while True:
      while device.commands_queue.qsize() > 10:
        await asyncio.sleep(_WAIT_FOR_EMPTY_QUEUE)
      device.queue_status()
      await asyncio.sleep(status_interval)

  def _register_views(self) -> None:
    domain_data = self.hass.data.setdefault(DOMAIN, {})
    domain_data[ACTIVE_CONTROLLER] = self
    if domain_data.get(VIEWS_REGISTERED):
      return
    self.hass.http.register_view(HisenseKeyExchangeView())
    self.hass.http.register_view(HisenseCommandsView())
    self.hass.http.register_view(HisensePropertyDatapointView())
    self.hass.http.register_view(HisensePropertyDatapointAckView())
    self.hass.http.register_view(HisenseNodePropertyDatapointView())
    self.hass.http.register_view(HisenseNodePropertyDatapointAckView())
    domain_data[VIEWS_REGISTERED] = True


def _controller_from_request(request: web.Request) -> HisenseController:
  hass = request.app["hass"]
  return hass.data[DOMAIN][ACTIVE_CONTROLLER]


class HisenseKeyExchangeView(HomeAssistantView):
  """Ayla LAN key exchange endpoint."""

  url = "/local_lan/key_exchange.json"
  name = "api:hisense_aircon:key_exchange"
  requires_auth = False

  async def post(self, request: web.Request) -> web.Response:
    return await _controller_from_request(request).handlers.key_exchange_handler(request)


class HisenseCommandsView(HomeAssistantView):
  """Ayla LAN command endpoint."""

  url = "/local_lan/commands.json"
  name = "api:hisense_aircon:commands"
  requires_auth = False

  async def get(self, request: web.Request) -> web.Response:
    return await _controller_from_request(request).handlers.command_handler(request)


class HisensePropertyDatapointView(HomeAssistantView):
  """Ayla LAN property update endpoint."""

  url = "/local_lan/property/datapoint.json"
  name = "api:hisense_aircon:property_datapoint"
  requires_auth = False

  async def post(self, request: web.Request) -> web.Response:
    return await _controller_from_request(request).handlers.property_update_handler(request)


class HisensePropertyDatapointAckView(HisensePropertyDatapointView):
  """Ayla LAN property update ack endpoint."""

  url = "/local_lan/property/datapoint/ack.json"
  name = "api:hisense_aircon:property_datapoint_ack"


class HisenseNodePropertyDatapointView(HisensePropertyDatapointView):
  """Ayla LAN node property update endpoint."""

  url = "/local_lan/node/property/datapoint.json"
  name = "api:hisense_aircon:node_property_datapoint"


class HisenseNodePropertyDatapointAckView(HisensePropertyDatapointView):
  """Ayla LAN node property update ack endpoint."""

  url = "/local_lan/node/property/datapoint/ack.json"
  name = "api:hisense_aircon:node_property_datapoint_ack"
