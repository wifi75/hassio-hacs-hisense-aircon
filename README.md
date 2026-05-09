# Hisense Air Conditioner for Home Assistant

Native Home Assistant custom integration for Hisense/Ayla LAN air conditioners.

This repository is now structured for HACS. It no longer runs as a Docker container, Home Assistant add-on, MQTT bridge, or external Python service. Home Assistant hosts the local Ayla LAN endpoints directly and communicates with the device on your local network.

## What This Integration Does

- Adds devices through the normal Home Assistant config flow.
- Discovers LAN keys from the supported Hisense/Ayla cloud account, or accepts manual LAN key entry.
- Registers unauthenticated local LAN endpoints under `/local_lan/...` so the air conditioner can exchange encrypted local messages with Home Assistant.
- Exposes the main device as a `climate` entity.
- Exposes additional writable properties as `switch`, `select`, and `number` entities.
- Exposes read-only device properties as `sensor` and `binary_sensor` entities.
- Does not require MQTT.

## Supported Setup Methods

### Cloud Discovery

Use this if the device is still visible in the original mobile app.

1. Install the integration through HACS as a custom repository.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & services -> Add integration**.
4. Search for **Hisense Air Conditioner**.
5. Choose **Discover from Hisense app**.
6. Enter:
   - app code, for example `hisense-eu`, `hisense-us`, `fglair-eu`
   - app username
   - app password
   - optional device name filter
   - Home Assistant HTTP port, usually `8123`
   - optional Home Assistant local IP if HA has multiple network interfaces or VLANs

After the integration has fetched the LAN key, the device can be blocked from the internet as long as it can still reach Home Assistant locally.

### Manual LAN Key Setup

Use this if you already know the device LAN key and key ID.

Enter:

- device name
- app code
- device IP address
- MAC address
- `lanip_key`
- `lanip_key_id`
- model
- temperature unit
- Home Assistant HTTP port
- optional Home Assistant local IP

## Network Notes

The air conditioner must be able to reach Home Assistant by plain HTTP on the configured port. The integration registers these local endpoints:

- `/local_lan/key_exchange.json`
- `/local_lan/commands.json`
- `/local_lan/property/datapoint.json`
- `/local_lan/property/datapoint/ack.json`
- `/local_lan/node/property/datapoint.json`
- `/local_lan/node/property/datapoint/ack.json`

If Home Assistant has several IP addresses or VLAN interfaces, set the **Home Assistant local IP address** option explicitly.

## Supported App Codes

Common codes include:

- `hisense-eu`
- `hisense-us`
- `hismart-eu`
- `hismart-us`
- `fglair-eu`
- `fglair-us`
- `field-us`
- `oem-eu`
- `oem-us`
- `mid-eu`
- `mid-us`
- `tornado-us`
- `york-us`
- `beko-eu`

The full list is available in `custom_components/hisense_aircon/app_mappings.py`.

## HACS Custom Repository

Add this repository in HACS as:

- Category: **Integration**
- Repository URL: this repository URL

Then install **Hisense Air Conditioner** and restart Home Assistant.

## Credits

The LAN protocol implementation is based on the original Ayla/Hisense AirCon project logic and has been repackaged as a native Home Assistant custom integration.

This project is not affiliated with Hisense, Ayla Networks, Fujitsu, or their subsidiaries.
