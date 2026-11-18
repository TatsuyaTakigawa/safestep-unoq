import os
import time

import safestep_config as cfg


def fire_alarm():
    """Update the trigger file. alarm_player.py (same container) plays the sound."""
    try:
        os.makedirs(os.path.dirname(cfg.TRIGGER_PATH), exist_ok=True)
        with open(cfg.TRIGGER_PATH, "w") as f:
            f.write(str(time.time()))
        return True
    except OSError as e:
        print(f"  -> alarm trigger failed ({type(e).__name__})")
        return False


def count_recent_reverse(reverse_times, now):
    """Drop old entries and return how many different people crossed in reverse recently."""
    old_ids = [t for t, ts in reverse_times.items() if now - ts > cfg.REVERSE_WINDOW_SEC]
    for tid in old_ids:
        del reverse_times[tid]
    return len(reverse_times)


def main():
    model = cfg.load_model()
    previous_side = {}
    reverse_times = {}   # track_id -> time of the latest reverse crossing
    last_alarm = None

    print(
        f"Start. LINE_Y={cfg.LINE_Y} MARGIN={cfg.MARGIN} "
        f"NORMAL_DIRECTION={cfg.NORMAL_DIRECTION}"
    )
    print(f"Camera: {cfg.camera_source()}  Audio: {cfg.AUDIO_DEVICE or 'default'}")
    print(
        f"Alarm: {cfg.REVERSE_THRESHOLD} people within {cfg.REVERSE_WINDOW_SEC}s, "
        f"cooldown {cfg.ALARM_COOLDOWN_SEC}s"
    )

    results = model.track(
        source=cfg.camera_source(),
        stream=True,
        classes=[0],
        persist=True,
        verbose=False,
    )

    for r in results:
        if r.boxes.id is None:
            continue

        ids = r.boxes.id.int().cpu().tolist()
        boxes = r.boxes.xyxy.cpu().tolist()

        for track_id, box in zip(ids, boxes):
            x1, y1, x2, y2 = box
            cy = (y1 + y2) / 2

            if cy < cfg.LINE_Y - cfg.MARGIN:
                side = "UP"
            elif cy > cfg.LINE_Y + cfg.MARGIN:
                side = "DOWN"
            else:
                continue

            if track_id in previous_side:
                old_side = previous_side[track_id]

                if old_side != side:
                    direction = side
                    is_reverse = direction != cfg.NORMAL_DIRECTION
                    label = "REVERSE" if is_reverse else "normal"
                    print(
                        f"ID:{track_id} LINE CROSS {old_side} -> {side} "
                        f"cy:{cy:.1f} [{label}]"
                    )

                    if is_reverse:
                        now = time.monotonic()
                        reverse_times[track_id] = now
                        count = count_recent_reverse(reverse_times, now)
                        print(
                            f"  -> reverse count in last {cfg.REVERSE_WINDOW_SEC}s: "
                            f"{count}/{cfg.REVERSE_THRESHOLD}"
                        )

                        if count >= cfg.REVERSE_THRESHOLD:
                            cooled_down = (
                                last_alarm is None
                                or now - last_alarm >= cfg.ALARM_COOLDOWN_SEC
                            )
                            if cooled_down:
                                print("  -> ALARM")
                                if fire_alarm():
                                    last_alarm = now
                                    reverse_times.clear()
                            else:
                                print("  -> threshold reached, but cooling down")

            previous_side[track_id] = side


if __name__ == "__main__":
    main()
