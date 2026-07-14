import aiohttp
import asyncio
from dataclasses import dataclass
from http import HTTPStatus
import json
import logging
import socket
import time

from .aircon import Device

_LOGGER = logging.getLogger(__name__)


@dataclass
class _NotifyConfiguration:
  device: Device
  headers: dict
  last_timestamp: int
  failures: int = 0
  next_attempt: float = 0


class Notifier:
  _KEEP_ALIVE_INTERVAL = 10.0
  _REQUEST_TIMEOUT = 5.0
  _TIME_TO_HANDLE_REQUESTS = 100e-3

  def __init__(self, port: int, local_ip: str, loop=None):
    self._configurations = []
    self._condition = asyncio.Condition()
    self._loop = loop

    self._running = False

    local_ip = local_ip or self._get_local_ip()
    self._json = {'local_reg': {'ip': local_ip, 'notify': 0, 'port': port, 'uri': '/local_lan'}}

  def _get_local_ip(self):
    sock = None
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      sock.connect(('10.255.255.255', 1))
      return sock.getsockname()[0]
    finally:
      if sock:
        sock.close()

  def register_device(self, device: Device):
    if device not in (conf.device for conf in self._configurations):
      headers = {
          'Accept': 'application/json',
          'Connection': 'keep-alive',
          'Content-Type': 'application/json',
          'Host': device.ip_address,
          'Accept-Encoding': 'gzip'
      }
      self._configurations.append(_NotifyConfiguration(device, headers, 0))

  async def _notify(self):
    async with self._condition:
      self._condition.notify_all()

  def notify(self):
    loop = self._loop or asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(self._notify(), loop)

  async def start(self, session: aiohttp.ClientSession):
    self._running = True
    async with self._condition:
      while self._running:
        queue_sizes = await asyncio.gather(*(self._perform_request(session=session, config=config)
                                             for config in self._configurations))
        if max(queue_sizes, default=0) <= 1:
          _LOGGER.debug('[KeepAlive] Waiting for notification or timeout')
          try:
            await asyncio.wait_for(self._condition.wait(), timeout=self._KEEP_ALIVE_INTERVAL)
          except asyncio.TimeoutError:
            pass
        else:
          # give some time to clean up the queues
          await asyncio.sleep(self._TIME_TO_HANDLE_REQUESTS)

  async def stop(self):
    self._running = False
    await self._notify()

  async def _perform_request(self, session: aiohttp.ClientSession,
                             config: _NotifyConfiguration) -> int:
    now = time.time()
    if now < config.next_attempt:
      return 0
    queue_size = config.device.commands_queue.qsize()
    if (queue_size == 0 or
        not config.device.available) and now - config.last_timestamp < self._KEEP_ALIVE_INTERVAL:
      return 0
    # A transient PUT refusal is common on these embedded Wi-Fi modules.
    # Retry registration with POST before declaring the device unavailable.
    method = 'PUT' if config.device.available and config.failures == 0 else 'POST'
    payload = {'local_reg': dict(self._json['local_reg'])}
    payload['local_reg']['notify'] = int(config.device.commands_queue.qsize() > 0)
    url = f'http://{config.device.ip_address}/local_reg.json'
    _LOGGER.debug('[KeepAlive] Sending %s %s %s', method, url, json.dumps(payload))
    try:
      timeout = aiohttp.ClientTimeout(total=self._REQUEST_TIMEOUT)
      async with session.request(method, url, json=payload, headers=config.headers,
                                 timeout=timeout) as resp:
        if resp.status != HTTPStatus.ACCEPTED.value:
          resp_data = await resp.text()
          _LOGGER.error(f'[KeepAlive] Sending local_reg failed: {resp.status}, {resp_data}')
          config.last_timestamp = now
          self._record_failure(config, now)
          if config.failures >= 3:
            config.device.available = False
          return 0
    except (aiohttp.ClientError, asyncio.TimeoutError) as ex:
      _LOGGER.warning(f'Failed to connect to {config.device.ip_address}, maybe it is offline: {ex}')
      config.last_timestamp = now
      self._record_failure(config, now)
      if config.failures >= 3:
        config.device.available = False
      return 0
    config.last_timestamp = now
    config.failures = 0
    config.next_attempt = 0
    config.device.available = True
    return queue_size

  @staticmethod
  def _record_failure(config: _NotifyConfiguration, now: float) -> None:
    """Apply capped exponential reconnect backoff."""
    config.failures += 1
    config.next_attempt = now + min(10, 2 ** min(config.failures, 4))
