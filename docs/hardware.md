# Hardware reference — Olympus / OM SYSTEM RS-27H

All identity values below were read off this machine on **2026-08-13** unless
marked otherwise. Values sourced from the web are labelled with their source and
flagged where unverified.

## Device identity (measured)

| Field | Value | How obtained |
| --- | --- | --- |
| USB vendor ID | `07b4` (Olympus Optical Co., Ltd) | `lsusb` |
| USB product ID | `0218` | `lsusb` |
| `usb.ids` label for `07b4:0218` | "Foot Switch RS-28" | `lsusb` |
| USB product string | `HID FootSwitch RS Series` | `udevadm` `ID_MODEL` |
| USB vendor string | `OLYMPUS CORPORATION` | `udevadm` `ID_VENDOR` |
| Serial number | `<serial>` | `udevadm` `ID_SERIAL_SHORT`, also evdev `Uniq` |
| evdev device name | `OLYMPUS CORPORATION HID FootSwitch RS Series` | `/proc/bus/input/devices` |
| evdev bus / version | bus `0x03` (USB), version `0x111` | `evemu-describe` |
| USB spec | `bcdUSB 1.10`, `bcdDevice 1.00`, `bcdHID 1.11` | `lsusb -v` |
| Endpoints | 1 interrupt IN, `wMaxPacketSize` 64 bytes, `bInterval` 10 | `lsusb -v` |
| Kernel driver | `usbhid` (in-tree, no vendor driver) | `udevadm` `ID_USB_DRIVER` |

**The `usb.ids` string says RS-28, the device string says "RS Series", and
neither is the model number.** `07b4:0218` is shared across the RS-series HID
foot switches — the USB descriptor does not distinguish RS-27H from RS-28H or
RS-31H. The RS-27H designation comes from the product listing, not from the bus.
Do not use `lsusb`'s "RS-28" label as evidence of which model this is.

### Device nodes

Stable paths, safe to hard-code in udev rules and remapper configs:

```
/dev/input/by-id/usb-OLYMPUS_CORPORATION_HID_FootSwitch_RS_Series_<serial>-event-mouse
/dev/input/by-id/usb-OLYMPUS_CORPORATION_HID_FootSwitch_RS_Series_<serial>-hidraw
```

On 2026-08-13 these resolved to `/dev/input/event17` and `/dev/hidraw0`. **The
`eventN` number is not stable across reboots or replug — always use the `by-id`
path.**

The `-event-mouse` suffix is misleading: udev applies it because `ID_INPUT_MOUSE=1`,
but the device advertises no `EV_REL` axes at all. It is a button-only device.

Permissions are `root:input 0660`, and the account is in the `input` group, so
reading the event node needs no `sudo`.

## Reported capabilities (measured)

`EV=13` → `EV_SYN` (0x00), `EV_KEY` (0x01), `EV_MSC` (0x04). No `EV_REL`, no
`EV_LED`, no `EV_ABS`.

Key codes advertised: the full `BTN_MISC` block, codes **256–271**
(`BTN_0` … `BTN_9` plus six unnamed codes). Raw `evemu-describe` output is in
[`captures/evtest-descriptor-2026-08-13.txt`](../captures/evtest-descriptor-2026-08-13.txt).

**Advertised capability is not actual behaviour.** Thirty-two button codes is a
generic descriptor shared across the RS series; this unit will emit only a small
subset. Which codes it actually emits is still unknown — see
[linux-integration.md](linux-integration.md#capturing-the-event-codes).

`bInterval 10` means the pedal is polled every 10 ms, so worst-case press-to-event
latency from the USB layer is ~10 ms. That is comfortably inside what push-to-talk
needs and is not a reason to prefer any other device.

## Connector and cabling

**The pedal does not have a captive USB cable.** The pedal body terminates in a
mini-DIN plug, and an interchangeable adapter cable converts that to the host
side. This is what makes the same pedal a USB device or an RS-232 device
depending on which cable is fitted, and it is why resellers describe the RS-27H
as "USB & RS232".

| Part | Description | Notes |
| --- | --- | --- |
| **KP-13** | Replacement **USB** adapter cable for the RS-27 foot switch | Mfr part `145163`. USB-A male on the host end, mini-DIN female on the pedal end. Listed ~$11.99 at Adorama (SKU `IOMKP13`), checked 2026-08-13 |
| — | RS-232 / DB9 adapter cable | Referenced by resellers as the serial option; no separate part number found |

**Pin count is unconfirmed.** The connector was observed on the physical unit as
8-pin. No vendor or reseller documentation published for this device states the
pin count — supplier listings say only "Mini-DIN Female". Mini-DIN is a family
of 3-to-9-pin patterns in a common 9.5 mm shell, mechanically keyed so a plug of
one pattern will not mate with a socket of another. So an 8-pin observation is
plausible and consistent, but it is **an observation, not a sourced fact**, and
buying a spare on the strength of it is a small risk.

**To order a spare, order the KP-13 by part number rather than by connector
description.** That sidesteps the pin-count question entirely: the KP-13 is
specified as the RS-27's USB cable, so it mates by definition. Ordering a generic
"8-pin mini-DIN to USB" cable does not, because the pinout is proprietary and
undocumented — mini-DIN says nothing about what the pins carry.

If the pinout itself is ever needed (for building an adapter rather than buying
one), the sources found on 2026-08-13 do not have it; it would have to come from
OM SYSTEM technical support or from metering the cable.

## Part numbers

| Field | Value |
| --- | --- |
| Retail listing name | "Olympus RS-27H 3-Button Footswitch with Keyboard Function" |
| Manufacturer part number | `V4521310U000` |
| Not this product | `147036` is the **older non-H RS-27**. Different product; do not order it as a replacement |

## Brand and spares availability

The Olympus audio/dictation business was divested and now trades as **OM Digital
Solutions / OM SYSTEM**; support and downloads live on `omsystem.com` domains,
not `olympus.com`. The USB descriptor still says `OLYMPUS CORPORATION` because it
is baked into old firmware. This matters for spares: search for both brand names,
and expect the RS-series accessories to be a long-tail transcription-market item
carried by specialist dictation resellers (TranscriptionGear, DictationOne,
Total Voice Technologies, HellerTek, TVPS) rather than mainstream electronics
retail.

## Not yet recorded

Read these off the unit and its base label, then fill in:

- Country of manufacture
- Cable length
- Dimensions and weight (one reseller listing says ~1.45 lb / 0.66 kg — unverified)
- Whether the box contained the RS-232 cable as well as the USB one
- Firmware/revision markings, if any
