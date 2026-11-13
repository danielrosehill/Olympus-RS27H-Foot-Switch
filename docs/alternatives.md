# Alternatives and rationale

Written 2026-08-13, after purchase, to check the choice against the obvious
alternative and to answer a specific worry about the hardware.

## Is the serial interface a warning sign?

The RS-27H does not have a captive USB cable. The pedal body ends in a mini-DIN
plug and an interchangeable adapter cable makes it USB or RS-232. That looks like
legacy baggage on a 2026 purchase. **It mostly isn't, and on balance it favours
this device rather than counting against it.**

Arguments that it is a sign of maturity, not decay:

- **The pedal itself contains no host interface.** It is a switch assembly with a
  connector. The bus-specific electronics live in the cable, which is why the same
  pedal has survived from RS-232 through USB. A device designed this way outlives
  the interface standard of its decade — the failure mode "the port is gone from
  modern machines" is fixed by a new cable, not a new pedal.
- **The cable is the wear item and it is separately replaceable.** On a foot
  device the cable is what gets trodden on, rolled over by a chair, and yanked.
  A captive cable makes that failure fatal to the whole unit. Here it is an
  ~$12 KP-13.
- **It is a professional transcription product, not a consumer peripheral.** That
  market values a decade of interoperability with installed software over
  following whatever connector is current, and it buys replacement parts. Long
  product life is the point.

Arguments that it is genuine legacy risk:

- **The connector pinout is proprietary and undocumented.** No public source
  gives the pin assignments; supplier listings say only "Mini-DIN Female". So the
  spare has to be bought as the vendor's `KP-13` part — a generic mini-DIN cable
  of the right pin count will not work, because mini-DIN specifies a shell, not a
  signalling scheme.
- **Single-source spares in a shrinking market.** The audio business is now OM
  Digital Solutions / OM SYSTEM and the parts are carried by specialist dictation
  resellers. If OM SYSTEM discontinues the KP-13, there is no drop-in substitute
  and no documentation to build one from.
- **USB 1.10, 10 ms polling.** Old silicon. Functionally irrelevant here — 10 ms
  is far below the threshold that matters for push-to-talk — but it confirms the
  design is not recent.

**Net: buy one spare KP-13 now rather than later.** That single action converts
the only real risk (single-source, undocumented, discontinuable cable) into a
non-issue for the life of the pedal, at about $12. It is the cheapest insurance
in this project, and the argument for it does not depend on any of the unresolved
questions elsewhere in this repo.

## Versus the Elgato Stream Deck Pedal

Checked 2026-08-13.

### Product status

The Stream Deck Pedal (`10GBF9901`, $89.99) launched **January 2022** and is
still the current and only Elgato pedal. **There is no 2026 model.** Elgato's
recent refreshes are elsewhere in the line: the 15-key Stream Deck MK2 gained a
scissor-key option (shipped by June 2026, still $149.99, membrane still offered),
and a Virtual Stream Deck beta puts up to 64 software buttons on Mac screens.

One caution for future searches: `bytebuys.com` claims a "2026 version" of the
pedal with improved hardware. No manufacturer or reputable outlet corroborates
this, and the site reads as SEO-generated. Its claims are more plausibly about
2026 *software* updates to the existing hardware. Do not treat it as a source.

### Comparison

| | Olympus RS-27H | Elgato Stream Deck Pedal |
| --- | --- | --- |
| Price | Transcription-market pricing | $89.99 |
| Pedals | 3 switches (vendor spec) | 3 |
| Cable | Detachable, mini-DIN + adapter (`KP-13`, ~$12) | Captive USB |
| Pedal tension | Fixed | Interchangeable springs |
| Linux support | Works as plain HID evdev, no software needed | Hardware is plain HID; **Elgato's Stream Deck software is Windows/macOS only** |
| Configuration | Firmware mode switch via Windows tool; not required | Designed around the Stream Deck app, which does not run on Linux |
| Multiple units | Not applicable | **Only one Stream Deck Foot Pedal can be used at a time** |
| Design intent | Professional transcription, all-day use | Streaming / content creation |

### Was the RS-27H the right call?

For this use case — push-to-talk dictation on a Linux desktop — **yes, and the
Stream Deck Pedal's advantages are mostly in a layer that Linux cannot reach.**

The Stream Deck Pedal's real selling point is the Stream Deck software: profiles,
multi-action macros, per-application switching. That software **does not run on
Linux**. Buying it for a Linux machine means buying the hardware and discarding
the reason it costs $90 — leaving a three-switch HID pedal that then needs
exactly the same evdev remapping layer the Olympus needs. Third-party projects
exist for the Stream Deck *key* devices on Linux, but relying on community
reimplementation of the vendor stack is a worse position than a device that needs
no vendor stack at all.

Against that, two things genuinely favour the Elgato and should be recorded
honestly:

- **Adjustable pedal tension** via interchangeable springs. For an all-day
  push-to-talk pedal, actuation force is an ergonomics variable that matters, and
  the Olympus does not offer it. If the RS-27H's tread turns out to be too heavy
  or too light in daily use, that is not adjustable.
- **A captive USB cable is simpler.** No adapter to lose, no proprietary spare to
  source.

Both are outweighed by the software-layer point. The decisive factor, though, is
neither of these: it is **whether the pedal reports true momentary press/release**,
and that is unverified on the Olympus and equally unverified on the Elgato. If the
capture shows the RS-27H fires canned events rather than holding, this comparison
reopens — and the Stream Deck Pedal becomes the fallback to test, not because it
is better designed for Linux, but because it is the only other three-switch pedal
readily available.

## Sources

- Vendor tool and modes: <https://audiosupport.omsystem.com/en/transcription/594-foot-switch-configuration-tool-guide/>
- Tool download, versions, supported models: <https://support.jp.omsystem.com/en/support/imsg/vtrek/download/software/rs27h/configuration_win.html>
- `footswitch2`: <https://sourceforge.net/projects/footswitch2/>
- B&H RS-27H listing: <https://www.bhphotovideo.com/c/product/1253869-REG/olympus_v4521310u000_3_button_footswitch_with_keyboard.html>
- KP-13: <https://www.adorama.com/iomkp13.html>
- Stream Deck Pedal at B&H: <https://www.bhphotovideo.com/c/product/1709819-REG/elgato_10gbf9901_stream_deck_foot_pedal.html>
- Elgato 2026 lineup: <https://appleinsider.com/articles/25/05/20/elgatos-new-stream-deck-lineup-goes-way-beyond-the-desktop>
