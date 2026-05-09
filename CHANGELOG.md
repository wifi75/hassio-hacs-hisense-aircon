# Changelog

## 1.0.0

- Converted the project from a Docker/Home Assistant add-on MQTT bridge into a native HACS custom integration.
- Added Home Assistant config flow with cloud discovery and manual LAN key setup.
- Added options flow for callback IP, Home Assistant HTTP port, and status refresh interval.
- Added native Home Assistant entities:
  - `climate`
  - `switch`
  - `select`
  - `number`
  - `sensor`
  - `binary_sensor`
- Moved the Ayla/Hisense LAN protocol implementation under `custom_components/hisense_aircon`.
- Removed Docker, MQTT, add-on, CLI, and SmartThings packaging files.
