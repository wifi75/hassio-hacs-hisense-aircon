# Changelog

## 1.2.2

- Stabilize device availability: transient keep-alive failures now trigger a POST re-registration retry and only mark the device unavailable after three consecutive failures. Reconnect backoff is capped at 10 seconds so controls no longer repeatedly turn grey after isolated Wi-Fi module refusals.

## 1.2.1

- Restore the last recorded current and target temperatures while waiting for the first post-restart LAN update. This keeps the thermostat temperature controls visible without reintroducing fabricated protocol defaults; fresh device reports always replace restored values.

## 1.2.0

- Entity and climate states now remain unknown until each value is genuinely reported by the device, eliminating all misleading startup placeholders without changing protocol-control defaults.
- Added automated tests and GitHub Actions validation plus tag-driven releases.
- Reduced entity clutter by disabling non-primary diagnostic entities by default and assigning them to the diagnostic category.
- Added English and Italian names for the main Hisense controls and sensors.
- Replaced the Home Assistant Super/Turbo restore thread timer with a cancellable event-loop task.
- Added privacy-safe downloadable diagnostics.
- Added capped reconnect backoff and safer per-device notifier payload handling.
- Hardened unauthenticated LAN endpoints with source-IP routing, bounded JSON bodies, stricter validation, and redacted logging.

## 1.1.22

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- Added complete Italian translations for the configuration flow, advanced settings, options form, validation errors, and setup descriptions.
- Renamed the English setup-flow title to "Add air conditioner" and its Italian counterpart to "Aggiungi climatizzatore". Home Assistant's integration-page button remains the core-generated "Add hub" label because this integration correctly has `integration_type: hub` and that button does not support integration-specific text.

## 1.1.21

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- Fixed the climate card briefly showing a bogus `81 °C` indoor temperature after Home Assistant restarts. The `f_temp_in` property now remains unknown until the air conditioner reports its first real temperature instead of starting from the legacy Fahrenheit placeholder `81.0`.

## 1.1.20

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- Added native English and Italian labels for the Hisense sleep profiles, replacing the raw protocol values `stop`, `one`, `two`, `three`, and `four` in the Home Assistant UI with meaningful names: Off/Common/Elderly/Youngsters/Children in English and Disattivata/Comune/Anziani/Giovani/Bambini in Italian.

## 1.1.19

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed fan speed still not restoring after Super/Turbo, even as a delayed separate command.** Debug logs from v1.1.18 confirmed temperature now restores correctly with the 3-second delay, but the AC kept ignoring fan speed specifically even when sent as its own separate `t_control_value` write. Fan speed is now sent as a fully standalone `t_fan_speed` property write (via a new `Device.force_standalone_command()` helper) instead of being packed into `t_control_value`, the same way already-reliable properties like `t_backlight`/`t_sleep` are sent. Fan mute and temperature continue to restore via the merged `t_control_value` write, since debug logs already confirmed those work that way.

## 1.1.18

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed fan speed not actually restoring when Super/Turbo is turned off**, confirmed with real debug logs: the software was correctly computing and sending a `t_control_value` write with the pre-Super fan speed, but the AC silently ignored the fan speed part whenever it was bundled in the *same* write as `heat_cold=OFF`, and kept reporting the Super-forced fan speed indefinitely. Turning Super off now sends `heat_cold=OFF` immediately, then sends the fan speed/mute/temperature restore as a *separate* `t_control_value` write about 3 seconds later, once the AC has had time to process leaving Super/Turbo mode.
- Verified end-to-end with an isolated simulation: fan speed and temperature are both correctly restored after the delayed second command is applied.

## 1.1.17

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed `t_fan_mute` (Quiet mode) never syncing from the device's reported status.** `AcDevice._update_controlled_properties()` derives and applies `t_power`, `t_fan_speed`, `t_work_mode`, `t_temp_heatcold`, `t_eco`, `t_temp`, and `t_fan_power` from every `t_control_value` the AC reports, but was missing `t_fan_mute` entirely -- so the Quiet switch in Home Assistant could silently drift out of sync with the AC's real state, and any code relying on the stored `t_fan_mute` (such as the Super/Turbo save-and-restore added in 1.1.15) could read a stale value.
- Investigating (not yet resolved): fan speed sometimes still doesn't restore correctly when Super/Turbo is turned off; needs further debug-log evidence to pin down whether this is a stale pre-Super value being saved, or the AC's own firmware not honoring the restore command immediately.

## 1.1.16

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Turning Super/Turbo off now also restores the target temperature**, not just fan speed/Quiet mode. The AC's own firmware forces the target temperature to its minimum while Super is active on its own (this integration never commands that), so the previously-set temperature is now saved before Super is turned on and restored -- merged into the same single `t_control_value` write -- when it's turned back off.

## 1.1.15

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Turning Super/Turbo off now restores the fan speed and Quiet mode that were active before it was turned on**, instead of permanently leaving them at the AUTO/unmuted values Super forces while active. The device remembers the fan speed/mute settings at the moment Super is switched on and re-applies them (merged into the same single `t_control_value` write as `heat_cold=OFF`, avoiding the same command race fixed in 1.1.14) the moment it's switched back off. If Super was already on before Home Assistant started tracking it (e.g. right after a restart), there's nothing to restore to, so turning it off just clears the Super bit as before.

## 1.1.14

Fork maintained by [Tiziano](https://github.com/wifi75) ([wifi75/hassio-hacs-hisense-aircon](https://github.com/wifi75/hassio-hacs-hisense-aircon)).

- **Fixed Super/Turbo (`t_temp_heatcold`) turning itself back off within a couple of seconds of being switched on.** Diagnosed from real debug logs (thanks to the 1.1.12 logging fix): turning Super on queued three *separate* `t_control_value` writes in a row (one each from `set_fast_heat_cold`, `set_fan_speed`, `set_fan_mute`), and each one read the AC's *currently stored* control register to build its update. Because that stored value is only refreshed once a previously queued command is actually dequeued and sent to the device, the second and third writes were built from the same stale, pre-change register and silently overwrote (cleared) the heat_cold bit the first write had just set. The device's own status echo in the logs confirmed this: heat_cold was reported `ON` once, then `OFF` two commands later, well before any reasonable turbo-timeout would apply.
- Turning Super on now computes one merged `t_control_value` (heat_cold=ON, fan_speed=AUTO, fan_mute=OFF) and sends it as a single command, eliminating the race. `t_sleep`/`t_temp_eight` continue to be sent as separate standalone commands, since they don't touch the packed register.
- Verified with an isolated simulation seeded with a real control-value snapshot captured from the user's device logs: before the fix, 3 competing `t_control_value` commands were queued; after the fix, exactly 1, correctly decoding to heat_cold=ON, fan_speed=AUTO, fan_mute=OFF.

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
