# Linux integration

## Short answer on Linux support

**No vendor software is needed to use this pedal on Linux, and none exists.**

The pedal binds to the in-tree `usbhid` driver and presents a normal evdev node
emitting `EV_KEY` events in the `BTN_MISC` range. Anything that can read evdev —
`input-remapper`, `keyd`, `evremap`, a Python `evdev` script, `interception-tools`
— can consume it today, matched on vendor `07b4` / product `0218` or on the
`by-id` path so it never collides with the real keyboard.

## Is there an open-source configuration tool?

Searched 2026-08-13. Findings:

| Candidate | What it actually is | Verdict for this device |
| --- | --- | --- |
| **`input-remapper`** | General evdev remapper with a GUI, per-device presets | **Already installed on this machine.** This is the tool. Not Olympus-specific, and does not need to be |
| `keyd` / `evremap` | General evdev remappers, config-file driven, no GUI | Viable alternatives to input-remapper; `keyd` is the better fit if the mapping ends up scripted rather than clicked |
| **`footswitch2`** (SourceForge) | A Linux *transcription playback application*, not a configurator. Tested against Vec Infinity in-USB2, Olympus RS28/RS31, MicroDia | Wrong shape for this use case — it is a media player with pedal control, not a remapping layer. RS-27H is not in its tested list |
| `rgerganov/footswitch` (GitHub) | Firmware programmer for PCsensor/Scythe-style pedals | Different vendor entirely — does not address `07b4` |
| Native port of the Olympus tool | Does not exist | No open-source reimplementation of the firmware mode-switch was found |

**There is no open-source equivalent of the vendor's Foot Switch Configuration
Tool**, i.e. nothing that writes the firmware operating mode from Linux. But for
this project that tool is not needed, and running it may be actively unhelpful —
see the next section.

## The vendor tool, and why running it is a decision not a formality

**Foot Switch Configuration Tool** (OM SYSTEM, Windows). Facts from the vendor
download page, checked 2026-08-13:

- Supported models: **RS27N, RS27H, RS28N, RS28H, RS31N, RS31H** — the RS-27H is
  in scope.
- Current version **2.0.1, April 2026**. 2.0.0 (April 2024) added the `N` models;
  1.0.1 (July 2021) reflected the Olympus → OM Digital Solutions rename.
- The page states **Windows 11** only, and lists no driver requirement — the only
  prerequisite is a free USB port.
- The support article for the tool describes it as covering RS-28H and RS-31H;
  the download page is broader. Treat the download page as authoritative.

### The two firmware modes

The tool's main function is switching a firmware-stored operating mode:

| Mode | HID class | Effect |
| --- | --- | --- |
| **Olympus mode** (renamed **"OM SYSTEM mode"** in v2.0.1) — the default | HID **vendor** class | Pedals report as vendor-defined buttons. What ODMS and DSS Player Pro expect |
| **Keyboard mode** | HID **keyboard** class | Each pedal is assigned a hotkey (e.g. `Ctrl+Alt+P`) or a multimedia key, and the device enumerates as a plain USB keyboard |

The mode is **written to the pedal and persists across machines** — flash it on
Windows and it stays that way on Linux.

### Recommendation: leave it in the default mode

The common internet advice is "flash it to Keyboard mode so it works without
drivers on Linux". **That advice does not apply here, and following it would make
this setup worse.** Reasons, in order of weight:

1. **It is already working.** The device is emitting `EV_KEY` events on evdev
   right now, with no vendor software, in the default mode. Keyboard mode solves
   a problem this machine does not have.
2. **Keyboard mode bakes the keystroke into firmware.** The required mapping is
   *context-dependent* — `Space` in Claude Code, `F13` everywhere else. Firmware
   cannot know which window has focus. A firmware-assigned key would have to be
   remapped in software anyway, so the firmware step buys nothing and adds a
   fixed keystroke that then has to be intercepted.
3. **It would make the pedal indistinguishable from a keyboard.** In vendor mode
   the pedal emits `BTN_0`-range codes that no keyboard ever produces, on its own
   evdev node. That is the cleanest possible thing to match on. In keyboard mode
   it emits ordinary key codes that must be distinguished from the real keyboard
   by device rather than by code — doable, but strictly more fragile.
4. **Keyboard mode risks breaking push-to-talk silently.** The per-pedal
   behaviour options are `Single (Press)`, `Double (Press/Release)` and
   `Long (Press/Hold)`. Only `Long` issues ON at press and OFF at release. The
   vendor documentation describes this as working "similarly" to a regular key
   press but stops short of guaranteeing hold semantics at protocol level. A
   pedal set to `Single` fires one keystroke and no release — which is exactly
   the failure mode that breaks push-to-talk without any visible error.

There is one **gotcha worth recording even if the tool is never used**: the
vendor support article warns *"Do not reopen the FTSW configuration tool to check
the settings, as this will change the mode of the foot switch."* Opening the tool
to verify a setting can silently alter it. If the tool is ever run, apply the mode,
close it, unplug and replug — and do not reopen it to confirm.

The tool's **Test tab** logs and timestamps presses, so if the pedal is taken to
a Windows machine anyway, that is a second way to answer the hold-vs-keystroke
question.

## Capturing the event codes

**Not yet done.** Three attempts on 2026-08-13 produced only the device
descriptor and zero press events.

### What went wrong (so it isn't repeated)

The first capture was started, then a second was started with
`pkill -f "evtest /dev/input/event17"` prefixed to kill the first.
**`pkill -f` matched the new command's own wrapper shell**, whose command line
contained that same string — so it killed the replacement capture along with the
old one. Both background jobs died with exit 144 and the output file held only
the 42-line `evtest` header.

Lesson, generic: never `pkill -f` a pattern that appears in the command line of
the shell issuing the `pkill`. Either use `pkill -x` on the process name, capture
the PID at launch, or start the new capture in a separate invocation.

### Working procedure

```bash
DEV=/dev/input/by-id/usb-OLYMPUS_CORPORATION_HID_FootSwitch_RS_Series_<serial>-event-mouse
OUT=~/pedal-capture-$(date +%Y%m%d-%H%M).txt

setsid timeout 120 evtest "$DEV" > "$OUT" 2>&1 < /dev/null &
```

`setsid` detaches it so it survives the parent shell. No `sudo` needed — the
account is in the `input` group. Confirm it is live by checking the file has the
~42-line header and that `pgrep -x evtest` returns a PID, *then* press.

### What to press, and what to look for

1. Two short taps.
2. One hold of ~3 seconds, then release.
3. **Every distinct pedal / switch zone on the unit, one at a time** — this is
   how the "one tread or three buttons" question gets settled. Vendor
   documentation says three switches; press everything pressable.

Then check three things in the log:

- **Which `code` values appear.** Expect a subset of 256–271. Record the mapping
  from physical pedal to code.
- **That each press produces `value 1` and each release produces `value 0`,** with
  a timestamp gap on the long hold matching how long the pedal was actually held.
  This is the momentary-HID test. If a press produces `value 1` immediately
  followed by `value 0` regardless of hold duration, the pedal is firing a canned
  event and **push-to-talk is not achievable with it** — which is the one finding
  that would rule the pedal out.
- **Whether `EV_MSC` / `MSC_SCAN` accompanies each press** (the device advertises
  `EV_MSC`), which reveals the underlying HID usage codes.

Raw output belongs in `captures/` with the date in the filename.

## Mapping plan

Not built yet. Recording the intended shape so the next session does not
re-derive it.

Target behaviour:

| Context | Pedal emits |
| --- | --- |
| Claude Code focused | `Space` |
| Everything else | `F13` |

`F13` is deliberate: no physical keyboard produces it, so nothing in the desktop
can conflict with it and any consumer binding to `F13` is unambiguously the pedal.

**`input-remapper` alone does not do this.** Its presets are per-device, not
per-focused-window — it has no notion of which application has focus. So the
context split has to come from somewhere else. Two shapes to evaluate when this
is picked up:

1. **Map once, branch downstream.** Pedal always emits `F13`; whatever handles
   the dictation binding decides what `F13` means based on focus. Simplest, keeps
   one static mapping, and means the pedal never emits `Space` at all — which
   avoids a stray `Space` landing in whatever has focus if the branch is wrong.
2. **Branch at the input layer.** A small evdev listener reads the pedal node
   directly (via `python-evdev` on the `by-id` path), checks the focused window,
   and synthesises `Space` or `F13` through `uinput`. More moving parts, but it
   is the only option if something downstream must genuinely receive `Space`.

Option 1 is the better default and should be tried first. Note that focus
detection is itself a live question on this desktop — under Wayland there is no
general cross-application way to read the focused window, so which compositor is
in use constrains the answer. Settle the event codes before spending time here.
