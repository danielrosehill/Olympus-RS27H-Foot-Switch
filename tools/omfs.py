#!/usr/bin/env python3
"""omfs: configure an OM System / Olympus RS27H/RS28H/RS31H (and N) foot switch from Linux.

Unofficial. Speaks the same HID protocol as OM Digital Solutions' "OM Foot Switch Configuration
Tool" 2.0.1 for Windows (protocol notes: docs/config-protocol.md). Standard library only; talks to
/dev/hidraw directly. Output is JSON.

  omfs.py info                              serial, USB mode, every pedal's binding
  omfs.py set left ctrl+shift+f13           bind a key chord (up to 6 keys + modifiers)
  omfs.py set center consumer:0xcd --double  bind a media/consumer usage, trigger on double press
  omfs.py usb-mode keyboard|vendor          persistent operating mode (what the Windows tool calls
                                            "Keyboard mode" / "OM SYSTEM mode")
  omfs.py backup > pedal.json ; omfs.py restore pedal.json
  omfs.py restore-defaults                  factory key bindings
"""
import argparse, glob, json, os, select, sys, time

VIDS = {0x07B4: "Olympus", 0x33A2: "OM Digital Solutions"}
PIDS = {0x0218: "RS27/RS28 (legacy)", 0x025F: "RS31 (legacy)", 0x0292: "RS27H/RS27N",
        0x0293: "RS28H/RS28N", 0x0294: "RS31H/RS31N"}

CMD_READ, CMD_WRITE, CMD_MODE, CMD_DEFAULTS = 0xE0, 0xE1, 0xE2, 0xE3
ITEM_STATUS, ITEM_SERIAL, ITEM_SHORTCUT, ITEM_USB_MODE = 1, 6, 23, 24
MSG = {0: "no-message", 1: "accepted", 2: "ignored"}

PEDALS = {"left": 0, "right": 1, "center": 2, "top": 3}         # top: RS31 only
PEDAL_NAMES = {v: k for k, v in PEDALS.items()}
TRIGGERS = {"long": 0, "single": 1, "double": 2}               # byte value in the shortcut record
TRIGGER_NAMES = {v: k for k, v in TRIGGERS.items()}
PAGE_KEYBOARD, PAGE_CONSUMER = 0x07, 0x0C
USB_MODES = {"vendor": 0x08, "keyboard": 0x18}                 # 0x18 = vendor|keyboard, what the tool writes
MODS = {"lctrl": 1, "ctrl": 1, "lshift": 2, "shift": 2, "lalt": 4, "alt": 4, "lsuper": 8, "super": 8,
        "meta": 8, "win": 8, "rctrl": 16, "rshift": 32, "ralt": 64, "altgr": 64, "rsuper": 128}

# HID keyboard page usages (HID Usage Tables 1.5, section 10)
KEYS = {chr(ord("a") + i): 0x04 + i for i in range(26)}
KEYS.update({str((i + 1) % 10): 0x1E + i for i in range(10)})
KEYS.update({f"f{i}": 0x3A + i - 1 for i in range(1, 13)})
KEYS.update({f"f{i}": 0x68 + i - 13 for i in range(13, 25)})
KEYS.update({"enter": 0x28, "esc": 0x29, "backspace": 0x2A, "tab": 0x2B, "space": 0x2C, "minus": 0x2D,
             "equal": 0x2E, "leftbrace": 0x2F, "rightbrace": 0x30, "backslash": 0x31, "semicolon": 0x33,
             "apostrophe": 0x34, "grave": 0x35, "comma": 0x36, "dot": 0x37, "slash": 0x38,
             "capslock": 0x39, "sysrq": 0x46, "scrolllock": 0x47, "pause": 0x48, "insert": 0x49,
             "home": 0x4A, "pageup": 0x4B, "delete": 0x4C, "end": 0x4D, "pagedown": 0x4E, "right": 0x4F,
             "left": 0x50, "down": 0x51, "up": 0x52, "numlock": 0x53, "menu": 0x65})
KEY_NAMES = {v: k for k, v in KEYS.items()}
# HID consumer page usages (section 15)
CONSUMER = {"playpause": 0xCD, "next": 0xB5, "previous": 0xB6, "stop": 0xB7, "fastforward": 0xB3,
            "rewind": 0xB4, "mute": 0xE2, "volumeup": 0xE9, "volumedown": 0xEA, "voicecommand": 0xCF,
            "record": 0xB2}
CONSUMER_NAMES = {v: k for k, v in CONSUMER.items()}


def find_device(path=None):
    """Return the hidraw node of interface 0 of a supported pedal."""
    if path:
        return path
    hits = []
    for node in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        try:
            uevent = open(f"{node}/device/uevent").read()
        except OSError:
            continue
        hid_id = next((l.split("=", 1)[1] for l in uevent.splitlines() if l.startswith("HID_ID=")), "")
        try:
            _, vid, pid = (int(x, 16) for x in hid_id.split(":"))
        except ValueError:
            continue
        if vid in VIDS and pid in PIDS:
            iface = os.path.realpath(f"{node}/device").split("/")[-2]   # e.g. 1-4:1.0
            hits.append((iface.endswith(":1.0"), f"/dev/{os.path.basename(node)}", vid, pid))
    if not hits:
        sys.exit(json.dumps({"ok": False, "error": "no OM/Olympus foot switch on any /dev/hidraw* "
                             "(attached to a VM? in a mode with no HID interface?)"}))
    hits.sort(reverse=True)                                             # interface 0 first
    return hits[0][1]


class Pedal:
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDWR)

    def close(self):
        os.close(self.fd)

    def _drain(self):
        while select.select([self.fd], [], [], 0)[0]:
            os.read(self.fd, 64)

    def command(self, cmd, item=0, payload=b"", timeout=0.5, expect_reply=True):
        buf = bytearray(64)
        buf[0], buf[1] = cmd, item
        buf[11:11 + len(payload)] = payload
        self._drain()
        os.write(self.fd, b"\x00" + bytes(buf))                     # report ID 0 + 64 bytes
        if not expect_reply:
            return None
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if select.select([self.fd], [], [], max(0, end - time.monotonic()))[0]:
                r = os.read(self.fd, 64)
                if len(r) > 9 and r[8] == cmd:                       # replies echo the command at [8]
                    return r
        raise TimeoutError(f"no reply to command 0x{cmd:02X} item {item}")

    def read_item(self, item, payload=b""):
        r = self.command(CMD_READ, item, payload)
        if r[4] != 1:
            raise RuntimeError(f"read item {item}: {MSG.get(r[4], r[4])}")
        return r

    def write_item(self, item, payload):
        r = self.command(CMD_WRITE, item, payload)
        if r[4] != 1:
            raise RuntimeError(f"write item {item}: {MSG.get(r[4], r[4])}")

    # --- items ---------------------------------------------------------------
    def serial(self):
        r = self.read_item(ITEM_SERIAL)
        return r[11:11 + r[10]].decode("utf-8", "replace")

    def usb_mode(self):
        return self.read_item(ITEM_USB_MODE)[10]

    def shortcut(self, pedal):
        r = self.read_item(ITEM_SHORTCUT, bytes([1, pedal]))
        return decode_shortcut(r[10:22])

    def set_shortcut(self, pedal, rec):
        rec = dict(rec, pedal=pedal)
        self.write_item(ITEM_SHORTCUT, encode_shortcut(rec))

    def set_usb_mode(self, mode):
        self.write_item(ITEM_USB_MODE, bytes([1, mode]))


def decode_shortcut(b):
    """b = response bytes from offset 10: pedal, page, trigger, modifiers, reserved, keys[6]."""
    pedal, page, trig, mods = b[0], b[1], b[2], b[3]
    out = {"pedal": PEDAL_NAMES.get(pedal, pedal), "trigger": TRIGGER_NAMES.get(trig, trig),
           "page": {PAGE_KEYBOARD: "keyboard", PAGE_CONSUMER: "consumer"}.get(page, page),
           "raw": b[:11].hex()}
    if page == PAGE_KEYBOARD:
        keys = [k for k in b[5:11] if k]
        out["modifiers"] = [n for n, v in MODS.items() if mods & v and n in
                            ("lctrl", "lshift", "lalt", "lsuper", "rctrl", "rshift", "ralt", "rsuper")]
        out["keys"] = [KEY_NAMES.get(k, f"0x{k:02x}") for k in keys]
        out["spec"] = "+".join([m[1:] if m.startswith("l") else m for m in out["modifiers"]] + out["keys"])
    elif page == PAGE_CONSUMER:
        usage = b[5] | (b[6] << 8)                                  # little-endian 16-bit usage
        out["usage"] = f"0x{usage:03x}"
        out["spec"] = f"consumer:{CONSUMER_NAMES.get(usage, hex(usage))}"
    return out


def encode_shortcut(rec):
    """-> 12-byte record written at offset 11: len(11), pedal, page, trigger, mods, 0, keys[6]."""
    b = bytearray(12)
    b[0], b[1], b[3] = 11, rec["pedal"], rec["trigger"]
    if rec["page"] == PAGE_CONSUMER:
        b[2] = PAGE_CONSUMER
        b[6], b[7] = rec["usage"] & 0xFF, (rec["usage"] >> 8) & 0xFF
    else:
        b[2], b[4] = PAGE_KEYBOARD, rec["mods"]
        for i, k in enumerate(rec["keys"][:6]):
            b[6 + i] = k
    return bytes(b)


def parse_spec(spec, trigger):
    """'ctrl+shift+f13', 'f15', '0x68', 'consumer:playpause', 'consumer:0xcf'."""
    spec = spec.lower().strip()
    if spec.startswith("consumer:"):
        v = spec.split(":", 1)[1]
        usage = CONSUMER[v] if v in CONSUMER else int(v, 0)
        return {"page": PAGE_CONSUMER, "usage": usage, "trigger": trigger}
    mods, keys = 0, []
    for part in spec.split("+"):
        if part in MODS:
            mods |= MODS[part]
        elif part in KEYS:
            keys.append(KEYS[part])
        else:
            keys.append(int(part, 0))
    if len(keys) > 6:
        sys.exit("at most 6 non-modifier keys")
    return {"page": PAGE_KEYBOARD, "mods": mods, "keys": keys, "trigger": trigger}


def record_from_decoded(d):
    trig = TRIGGERS.get(d["trigger"], d["trigger"])
    raw = bytes.fromhex(d["raw"])
    if raw[1] == PAGE_CONSUMER:
        return {"page": PAGE_CONSUMER, "usage": raw[5] | (raw[6] << 8), "trigger": trig}
    return {"page": PAGE_KEYBOARD, "mods": raw[3], "keys": [k for k in raw[5:11] if k], "trigger": trig}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", help="hidraw node (default: auto-detect interface 0)")
    ap.add_argument("--pedals", type=int, default=3, help="3 (RS27/28) or 4 (RS31)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info"); sub.add_parser("backup"); sub.add_parser("restore-defaults")
    s = sub.add_parser("set"); s.add_argument("pedal", choices=PEDALS); s.add_argument("spec")
    g = s.add_mutually_exclusive_group()
    for t in TRIGGERS:
        g.add_argument(f"--{t}", dest="trigger", action="store_const", const=TRIGGERS[t])
    m = sub.add_parser("usb-mode"); m.add_argument("mode", choices=USB_MODES)
    r = sub.add_parser("restore"); r.add_argument("file")
    p = sub.add_parser("probe", help="read an arbitrary item (research)")
    p.add_argument("item", type=lambda x: int(x, 0)); p.add_argument("payload", nargs="?", default="")
    a = ap.parse_args()

    dev = Pedal(find_device(a.device))
    try:
        if a.cmd in ("info", "backup"):
            mode = dev.usb_mode()
            out = {"device": dev.path, "serial": dev.serial(), "usb_mode": mode,
                   "usb_mode_name": {v: k for k, v in USB_MODES.items()}.get(mode, "unknown"),
                   "pedals": [dev.shortcut(i) for i in range(a.pedals)]}
        elif a.cmd == "set":
            rec = parse_spec(a.spec, TRIGGERS["single"] if a.trigger is None else a.trigger)
            dev.set_shortcut(PEDALS[a.pedal], rec)
            out = {"ok": True, "now": dev.shortcut(PEDALS[a.pedal])}
        elif a.cmd == "usb-mode":
            dev.set_usb_mode(USB_MODES[a.mode])
            out = {"ok": True, "usb_mode": dev.usb_mode(), "note": "takes effect after replug"}
        elif a.cmd == "restore":
            data = json.load(open(a.file))
            for d in data["pedals"]:
                dev.set_shortcut(PEDALS[d["pedal"]] if isinstance(d["pedal"], str) else d["pedal"],
                                 record_from_decoded(d))
            out = {"ok": True, "restored_from": a.file, "pedals": len(data["pedals"])}
            if dev.usb_mode() != data["usb_mode"]:
                dev.set_usb_mode(data["usb_mode"])          # refused by fw 1.01 on 2026-11-14, see docs
                out["usb_mode"] = data["usb_mode"]
        elif a.cmd == "restore-defaults":
            r = dev.command(CMD_DEFAULTS)
            out = {"ok": r[4] == 1, "reply": MSG.get(r[4], r[4])}
        elif a.cmd == "probe":
            r = dev.command(CMD_READ, a.item, bytes.fromhex(a.payload))
            out = {"item": a.item, "message": MSG.get(r[4], r[4]), "reply": r.hex()}
    finally:
        dev.close()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
