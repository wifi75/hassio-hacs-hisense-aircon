# Changelog

## 1.1.3

- Added configurable device temperature units for cloud setup and integration options.
- Used Home Assistant's configured temperature unit as the fallback when cloud discovery cannot determine the device unit.
- Defaulted manual setup temperature units from Home Assistant instead of hardcoding Celsius.

## 1.1.2

- Fixed the collapsed Advanced Settings section so default values do not block cloud setup validation.
- Fixed Home Assistant section translations so the Advanced Settings heading and help text are visible.
- Added direct setup links to the Supported App Codes README section and corrected manifest repository links.

## 1.1.1

- Improved README documentation with upstream device notes, app-code prerequisites, and available properties.
- Simplified cloud setup so only app code, username, and password are shown by default.
- Moved optional cloud setup fields into a collapsed Advanced Settings section with clearer explanations.

## 1.1.0

- Ported recent community fork fixes for sleep mode, control-value work mode updates, and swing command handling.
- Added FGLair temperature scaling, half-degree target steps, display/outdoor temperature parsing, fan-only mode, diffuse fan mode, powerful mode, outdoor low noise, and refresh/get-prop controls.
- Added vertical swing angle support as a native Home Assistant select entity.
- Improved local registration keepalive handling with request timeouts and offline availability updates.
- Hardened property parsing and encrypted update logging for malformed payloads.

## 1.0.1

- Added browser-friendly `GET` explanations on real Hisense/Ayla LAN endpoints.
- Added root compatibility aliases for `/key_exchange.json` and `/commands.json`.
- Kept `/local_lan/commands.json` as a real `GET` protocol endpoint for requests that come from the configured air conditioner IP.

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
