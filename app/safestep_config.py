"""SafeStep AI (UNO Q) shared settings. Everything can be overridden by environment variables."""
import glob
import os
import re


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        raise SystemExit(f"Environment variable {name} must be an integer")


def _float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        raise SystemExit(f"Environment variable {name} must be a number")


APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)

MODEL_PATH = os.environ.get(
    "SAFESTEP_MODEL", os.path.join(ROOT_DIR, "models", "yolo26n_ncnn_model")
)

# Virtual line (same defaults as the Raspberry Pi version).
LINE_Y = _int("SAFESTEP_LINE_Y", 240)
MARGIN = _int("SAFESTEP_MARGIN", 20)

# Direction treated as normal. The opposite is reported as reverse.
NORMAL_DIRECTION = os.environ.get("SAFESTEP_NORMAL_DIRECTION", "DOWN").upper()
if NORMAL_DIRECTION not in ("UP", "DOWN"):
    raise SystemExit("SAFESTEP_NORMAL_DIRECTION must be UP or DOWN")

# Alarm settings
REVERSE_WINDOW_SEC = _int("SAFESTEP_REVERSE_WINDOW_SEC", 30)
REVERSE_THRESHOLD = _int("SAFESTEP_REVERSE_THRESHOLD", 1)
ALARM_COOLDOWN_SEC = _int("SAFESTEP_ALARM_COOLDOWN_SEC", 0)

# Alarm player (runs in the same container as the detector)
TRIGGER_PATH = os.environ.get("SAFESTEP_TRIGGER", "/tmp/safestep/trigger")
AUDIO_PATH = os.environ.get(
    "SAFESTEP_AUDIO_FILE", os.path.join(APP_DIR, "warning_audio", "alert.wav")
)


ASOUND_DIR = "/proc/asound"


def _find_usb_audio():
    """First USB sound card that can PLAY audio, as an ALSA device (e.g. plughw:1,0).
    USB webcams show up as USB-Audio too (microphone only), so capture-only cards are skipped."""
    try:
        with open(os.path.join(ASOUND_DIR, "cards")) as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    for line in lines:
        m = re.match(r"\s*(\d+)\s+\[.*?\]:\s*USB-Audio", line)
        if m and glob.glob(os.path.join(ASOUND_DIR, f"card{m.group(1)}", "pcm*p")):
            return f"plughw:{m.group(1)},0"
    return None


# e.g. plughw:1,0. Empty = auto-detect a USB sound card, else the ALSA default.
AUDIO_DEVICE = os.environ.get("SAFESTEP_AUDIO_DEVICE") or _find_usb_audio() or ""
GAP_SEC = _float("SAFESTEP_GAP_SEC", 3.0)

# Speaker volume (0-100) applied to the ALSA mixer at startup. Unset = leave the mixer as it is.
_vol = os.environ.get("SAFESTEP_VOLUME", "").strip()
VOLUME_PERCENT = max(0, min(100, int(_vol))) if _vol.isdigit() else None
POLL_SEC = 0.2


def _find_usb_camera():
    """Index N of the first USB camera capture node (/dev/videoN). None if not found.
    The UNO Q has internal video devices, so /dev/video0 is not necessarily the USB camera."""
    base = "/sys/class/video4linux"
    try:
        names = [n for n in os.listdir(base) if n[5:].isdigit() and n.startswith("video")]
    except OSError:
        return None
    for n in sorted(names, key=lambda x: int(x[5:])):
        try:
            with open(os.path.join(base, n, "index")) as f:
                if f.read().strip() != "0":
                    continue
            if "/usb" not in os.path.realpath(os.path.join(base, n, "device")):
                continue
        except OSError:
            continue
        if os.path.exists(f"/dev/{n}"):
            return int(n[5:])
    return None


def camera_source():
    """SAFESTEP_CAMERA: "auto" (default) = USB camera, a number = /dev/videoN, or a path/URL."""
    v = os.environ.get("SAFESTEP_CAMERA", "auto")
    if v == "auto":
        found = _find_usb_camera()
        return found if found is not None else 0
    return int(v) if v.isdigit() else v


def load_model():
    from ultralytics import YOLO, settings

    # No telemetry / network access at runtime.
    try:
        settings.update({"sync": False})
    except Exception:
        pass
    return YOLO(MODEL_PATH)
