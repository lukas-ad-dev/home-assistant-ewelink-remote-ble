# eWeLink Remote BLE for Home Assistant

Local Home Assistant support for the **SONOFF SwitchMan R5** without an
eWeLink-Remote gateway.

The integration decodes the R5's passive Bluetooth advertisements and exposes
every physical remote as a normal Home Assistant device. Each R5 can be named,
assigned to an area, and used in device-based automations.

## Features

- One Home Assistant device per physical R5
- Automatic discovery of additional R5 remotes
- Six event entities per R5, with their physical positions in the name
- Device automation triggers for every button and action
- Short press, double press, hold start, hold repeat, and hold release
- Fully local operation; no eWeLink account or cloud connection
- Multiple BLE receivers/proxies can hear the same remote without duplicate events
- English and German translations

## Button layout

| Position | Top row | Bottom row |
| --- | --- | --- |
| Left | Button 1 | Button 4 |
| Middle | Button 2 | Button 5 |
| Right | Button 3 | Button 6 |

Each button exposes these event types:

| Event type | Meaning |
| --- | --- |
| `single` | Short press |
| `double` | Double press |
| `hold_start` | Long press started |
| `hold_repeat` | Additional packet while held |
| `hold_release` | Button was released after a hold |

The R5 does not transmit a dedicated release packet. `hold_release` is therefore
generated locally after 1.6 seconds without another hold packet. This makes the
event useful for dimming and cover stop actions, but it has a small intentional
delay.

## Requirements

- Home Assistant with the Bluetooth integration enabled
- A receiver that forwards the **raw BLE advertisement** to Home Assistant
- The [BLE Passthrough integration](https://github.com/iHost-Open-Source-Project/ble_passthrough)
  or an equivalent source that supplies `BluetoothServiceInfoBleak.raw`

Tested with Home Assistant 2026.11 and an SMLIGHT SLZB-MR4U running SLZB-OS.

> [!IMPORTANT]
> A Bluetooth proxy is not the same thing as an eWeLink-Remote gateway. This
> integration does not pair the R5 and does not emulate the proprietary gateway.
> It passively decodes the R5 broadcasts that a compatible receiver forwards to
> Home Assistant.

## Installation with HACS

1. Open HACS in Home Assistant.
2. Open **Integrations**, then **Custom repositories**.
3. Add `https://github.com/lukas-ad-dev/home-assistant-ewelink-remote-ble` as an
   **Integration** repository.
4. Install **eWeLink Remote BLE** and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **eWeLink Remote BLE** and complete the empty setup form.
7. Press any R5 button once. The remote appears as a new device with six event
   entities.

## Manual installation

Copy the directory
`custom_components/ewelink_remote_ble` into your Home Assistant configuration
directory, restart Home Assistant, and then add the integration from
**Settings → Devices & services**.

## Areas and multiple remotes

Every physical R5 has its own stable device identifier. Open the device, select
**Edit**, and choose its area. A second R5 is discovered as a separate device and
can be assigned to another area. The six buttons remain entities of that remote;
they are not incorrectly created as six separate devices.

## Automation example

For a cover, a typical setup is:

- Button 1 `single`: open the cover completely
- Button 1 `hold_start`: start opening
- Button 1 `hold_release`: stop
- Button 3 `single`: close the cover completely
- Button 3 `hold_start`: start closing
- Button 3 `hold_release`: stop

Choose the R5 under **Device** when creating an automation, then select the
button and action. The event entities can also be used directly as state/event
triggers.

## Troubleshooting

- **Device does not appear:** verify that BLE Passthrough receives raw
  advertisements, then press an R5 button.
- **Device exists but has no entities:** restart Home Assistant after updating
  this integration to version 0.3.0 or later.
- **Hold release feels delayed:** this is expected because the R5 has no release
  packet; the integration waits 1.6 seconds after the last hold broadcast.
- **Duplicate receivers:** duplicates from multiple gateways are suppressed using
  the R5 sequence counter.

## Credits and disclaimer

Protocol research and the public test vector were informed by
[Flobul/Tasmota-eWeLinkRemote](https://github.com/Flobul/Tasmota-eWeLinkRemote).
BLE forwarding is provided by the separate BLE Passthrough project.

This is an independent community integration and is not affiliated with SONOFF
or CoolKit/eWeLink.

## License

MIT License. See [LICENSE](LICENSE).
