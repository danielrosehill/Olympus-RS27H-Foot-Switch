# Olympus RS-27H foot switch — Linux integration

Working notes for the Olympus / OM SYSTEM **RS-27H** USB foot switch (August 2026). Covers what the device is, what it looks like to
the Linux input stack, how it gets configured, and how to source a spare.

Opened 2026-08-13. The per-unit USB serial is replaced with `<serial>` throughout.

## Status

| Item | State |
| --- | --- |
| Device recognised by Linux | **Confirmed** — enumerates as a HID device, no driver needed |
| USB / evdev identity recorded | **Confirmed** — see [docs/hardware.md](docs/hardware.md) |
| Per-pedal event codes captured | **Not done** — capture window ran, no presses were recorded; parked 2026-08-13 |
| Number of physical pedals | **Unresolved** — vendor documents 3 buttons, unit was described as one tread; see below |
| Momentary (hold) vs canned keystroke | **Not verified** — this is the load-bearing question for push-to-talk |
| Vendor config tool run | Not yet — Windows-only, planned on a Windows machine |
| Context-dependent mapping built | Not started |

## The goal this device was bought for

Push-to-talk dictation while both hands stay on keyboard and mouse. The target
mapping is context-dependent:

- in **Claude Code** → the pedal acts as `Space`
- **everywhere else** → the pedal acts as `F13`

`F13` is chosen because no physical keyboard emits it, so nothing else in the
desktop can collide with it. See [docs/linux-integration.md](docs/linux-integration.md)
for how that mapping is intended to work and why the vendor's Windows tool is
the wrong layer to put it in.

## Pedal event codes (captured 2026-11-14)

Three independent switches, confirmed by pressing each one with `evtest` on the
default (vendor) firmware mode. The kernel names are mouse-button names and are
**mirrored**: the left pedal is not `BTN_LEFT`.

| Physical pedal | Code | evdev name |
| --- | --- | --- |
| Left | 274 | `BTN_MIDDLE` |
| Centre | 273 | `BTN_RIGHT` |
| Right | 272 | `BTN_LEFT` |

All three are momentary: one press is `value 1` on press and `value 0` on
release, with no auto-repeat (`value 2`) events. A 2.7 s hold on the centre pedal
produced a single press and a single release, so hold-to-talk works without
vendor configuration. Raw capture: `captures/evtest-presses-2026-11-14.txt`.

Capture gotchas: input-remapper grabs the device, so stop its preset first
(`input-remapper-control --command stop --device "OLYMPUS CORPORATION HID
FootSwitch RS Series"`) and restart it afterwards with `--command start ...
--preset Control`. Run evtest as `stdbuf -oL evtest` when redirecting to a file,
otherwise a `timeout` kill discards the buffered output and the capture looks
empty.

## Layout

| Path | Contents |
| --- | --- |
| `docs/hardware.md` | Device identity, connector, part numbers and spares |
| `docs/linux-integration.md` | evdev findings, config tooling, the mapping plan, how to resume the capture |
| `docs/alternatives.md` | Stream Deck Pedal comparison and whether the serial heritage is a red flag |
| `captures/` | Raw `evtest` and `lsusb` output, dated |

## Resuming the event capture

Not done yet, and it is the next step. Exact procedure and the mistake that
wasted the first three attempts are in
[docs/linux-integration.md](docs/linux-integration.md#capturing-the-event-codes).
