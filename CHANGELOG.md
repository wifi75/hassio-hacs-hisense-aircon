# Changelog

## 1.1.13

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed the "Super"/Turbo switch (`t_temp_heatcold`) throwing "unknown error" when turned on.** Enabling Turbo mode automatically also sends `t_temp_eight OFF` as a side effect, but `t_temp_eight` was one of several writable properties with no representation in the packed `t_control_value` register, so once the AC had reported that register, this follow-up command raised `ValueError` and Home Assistant surfaced it as `switch/turn_on unknown error`.
- **Audited every writable property against `control_value.py` and fixed all similarly affected properties at once**, instead of one at a time: `t_temp_eight`, `t_setmulti_value`, `t_device_info`, `t_ftkt_start`, and `t_run_mode` are now sent as standalone commands (like `t_backlight`/`t_display_power` were fixed in 1.1.11), since none of them have a corresponding pack/unpack function in `control_value.py`.
- Refactored the standalone-property list into a single `Device._STANDALONE_PROPERTIES` class constant instead of an inline tuple, to make future audits easier.

## 1.1.12

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed per-integration debug logging.** `aircon.py`, `notifier.py`, and `query_handlers.py` called the bare `logging` module directly instead of a module-scoped logger, so all of this integration's debug/info/warning/error messages (including the `[KeepAlive]` LAN notifier logs and the encrypted command/property traffic logs) were emitted under the Python root logger. Setting `custom_components.hisense_aircon: debug` via `logger.set_level` (or in `configuration.yaml`) had no effect on them. All three files now use a proper `_LOGGER = logging.getLogger(__name__)`, so debug logging for this integration actually works.
- **Diagnosed (not yet fixed): intermittent LAN connectivity to the AC.** While investigating the backlight/display-power switches, logs showed `Failed to connect to <device IP>, maybe it is offline: [Errno 104] Connection reset by peer` from the LAN keep-alive notifier (`notifier.py`), meaning Home Assistant's periodic "wake up and check for commands" request to the AC was actively refused by the device at least once. If this keeps happening, queued commands (including backlight/display power) may sit unsent until the AC's own next periodic poll. This looks like a device/network-level issue rather than a bug in this integration, and needs further investigation with proper debug logs now that they work.

## 1.1.11

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed the display/backlight switch not working on `AcDevice` models.** Once the air conditioner reports its packed `t_control_value` register (which happens after the first status update), `queue_command()` routes every write through `AcDevice._convert_to_control_value()`. That method only knows how to pack power, mode, fan, temperature, eco, and swing settings — it has no case for `t_backlight` or `t_display_power`, so toggling the "Backlight"/"Display Power" switch silently raised `ValueError` and never sent anything to the device (this is why the physical remote could still turn the display off, but the Home Assistant toggle could not). `t_backlight` and `t_display_power` are now sent as standalone commands, the same way `t_sleep` and `t_swing_angle` already were.

## 1.1.10

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Added a "Visit" link on each device's info page** pointing to this fork's GitHub repository, using Home Assistant's standard `configuration_url` device field.

## 1.1.9

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed the integration logo not showing up in Home Assistant.** 1.1.8 added `custom_components/hisense_aircon/icon.svg` and a `"logo"` key in `manifest.json`, but neither is a mechanism Home Assistant actually reads — the manifest schema has no `logo` field, and integration icons are served from a dedicated `brand/` folder as PNG, not from an arbitrary file referenced in the manifest. The icon now lives at `custom_components/hisense_aircon/brand/icon.png` (plus `icon@2x.png` for hDPI), which Home Assistant 2026.3+ picks up automatically with no manifest changes required. Older Home Assistant versions simply fall back to the generic placeholder — the integration itself is unaffected.
- Removed the non-functional `"logo"` key from `manifest.json`.
- Fixed `codeowners` in `manifest.json` to use the `@username` GitHub-handle format Home Assistant expects (`@wifi75`) instead of a plain display name.

## 1.1.8

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed multi-device LAN support.** Previously, adding a second manually configured local device silently broke the first one: all LAN HTTP endpoints (`/local_lan/...`) resolved to a single globally-shared `ACTIVE_CONTROLLER`, so the most recently added config entry overwrote every earlier one. Requests are now routed to the correct controller by matching the requesting device's IP address against each controller's own registered devices, so any number of local devices can run side by side.
- **Enabled multiple config entries.** `single_config_entry` was `true` in the manifest, which made Home Assistant block adding a second "Hisense Air Conditioner" integration entry entirely, regardless of the underlying code support. It is now `false`, so `Settings -> Devices & services -> Add integration` can be used repeatedly to add as many local or cloud-discovered devices as needed.
- **Added a custom logo** (`icon.svg`) so the integration displays a distinct icon in Home Assistant's integration list, device pages, and the HACS store, instead of the generic placeholder.
- Updated `manifest.json` with author/maintainer/documentation/issue-tracker links for this fork.

## 1.1.7

- Run the LAN notifier and status polling loops as background tasks so they do not delay Home Assistant startup.

## 1.1.6

- Scheduled entity state writes on the Home Assistant event loop so LAN availability and property updates are applied safely from update callbacks.

## 1.1.5

- Replaced raw protocol-style property names with friendly Home Assistant entity names.
- Added `hisense_property` and `description` attributes to property entities for protocol context.
- Documented the `t_`, `f_`, and `f_e_` protocol prefixes in the README.

## 1.1.4

- Added an explicit cloud discovery step for selecting one or more discovered air conditioners.
- Selected all discovered devices by default so multi-device accounts can be added in one setup flow.
- Updated setup documentation to describe the multi-device selection step.

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
