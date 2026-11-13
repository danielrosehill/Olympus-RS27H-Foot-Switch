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

## Open question: how many pedals does this unit have?

Every vendor and reseller source describes the RS-27H as a **3-button** foot
switch (B&H sells it as "RS-27H 3-Button Footswitch with Keyboard Function").
The unit in hand was described as the variant with a single tread surface.

These may not conflict — a single wide treadle plate can carry three switch
zones — but it is not settled, and it changes how many event codes we expect.
Resolve it by looking at the unit and by finishing the event capture. Until then
treat "one pedal" as an observation about the physical surface, not about the
number of switches.

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
