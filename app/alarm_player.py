import os
import re
import subprocess
import sys
import time
import wave

import safestep_config as cfg


def wav_seconds(path):
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None


def get_mtime():
    try:
        return os.stat(cfg.TRIGGER_PATH).st_mtime_ns
    except FileNotFoundError:
        return None


def apply_volume():
    """Set every playback volume control of the output card to SAFESTEP_VOLUME percent."""
    vol = cfg.VOLUME_PERCENT
    if vol is None:
        return
    m = re.match(r"(?:plug)?hw:(\d+)", cfg.AUDIO_DEVICE)
    card = m.group(1) if m else "0"
    try:
        out = subprocess.run(
            ["amixer", "-c", card, "scontents"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Cannot read the mixer ({type(e).__name__}). Volume not set.")
        return

    names = []
    for block in out.split("Simple mixer control ")[1:]:
        head = block.splitlines()[0]
        name = re.match(r"'([^']+)'", head)
        if name and re.search(r"Capabilities:.*\bpvolume\b", block):
            names.append(name.group(1))
    if not names:
        print(f"No playback volume control on card {card}. Volume not set.")
        return

    for name in names:
        ok = subprocess.run(
            ["amixer", "-q", "-c", card, "sset", name, f"{vol}%", "unmute"]
        ).returncode == 0
        if not ok:  # controls without a mute switch
            ok = subprocess.run(
                ["amixer", "-q", "-c", card, "sset", name, f"{vol}%"]
            ).returncode == 0
        print(f"Volume {vol}% on card {card} '{name}': {'OK' if ok else 'failed'}")


def play(path):
    """Start playing the file. Returns the process, or None on failure."""
    cmd = ["aplay", "-q"]
    if cfg.AUDIO_DEVICE:
        cmd += ["-D", cfg.AUDIO_DEVICE]
    cmd.append(path)
    try:
        return subprocess.Popen(cmd)
    except OSError as e:
        print(f"Cannot start aplay ({type(e).__name__})")
        return None


def main():
    path = cfg.AUDIO_PATH
    if not os.path.isfile(path):
        print(f"Sound file not found: {path}")
        sys.exit(1)

    sec = wav_seconds(path)
    if sec is None:
        print(f"Cannot read as WAV: {path}")
        sys.exit(1)
    print(
        f"Sound file: {os.path.basename(path)} ({sec:.1f} sec), gap {cfg.GAP_SEC:.1f} sec, "
        f"device: {cfg.AUDIO_DEVICE or 'default'}"
    )

    apply_volume()

    if "--test" in sys.argv:
        proc = play(path)
        if proc is not None:
            sys.exit(proc.wait())
        sys.exit(1)

    os.makedirs(os.path.dirname(cfg.TRIGGER_PATH), exist_ok=True)
    with open(cfg.TRIGGER_PATH, "a"):
        pass

    last_mtime = get_mtime()
    proc = None
    pending = False        # a detection is waiting to be played
    next_allowed = 0.0     # no playback may start before this time (monotonic)
    print(f"Alarm player started. Watching {cfg.TRIGGER_PATH}")

    try:
        while True:
            mtime = get_mtime()
            if mtime is not None and mtime != last_mtime:
                last_mtime = mtime
                if pending:
                    print("Trigger detected. Already waiting to play.")
                elif proc is not None or time.monotonic() < next_allowed:
                    print("Trigger detected. Will play after the current sound.")
                else:
                    print("Trigger detected.")
                # Many detections during playback are merged into one more playback.
                pending = True

            if proc is not None and proc.poll() is not None:
                if proc.returncode != 0:
                    print(f"aplay failed (exit {proc.returncode}). Check SAFESTEP_AUDIO_DEVICE.")
                # The playback has just finished: start the gap.
                proc = None
                next_allowed = time.monotonic() + cfg.GAP_SEC

            if pending and proc is None and time.monotonic() >= next_allowed:
                pending = False
                print("Playing sound.")
                proc = play(path)
                if proc is None:
                    next_allowed = time.monotonic() + cfg.GAP_SEC

            time.sleep(cfg.POLL_SEC)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopped.")
        if proc is not None and proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main()
