import time

import safestep_config as cfg

PRINT_INTERVAL_SEC = 0.3


def main():
    model = cfg.load_model()
    last_print = {}

    print("Observation mode. Walk through the stairs. Press Ctrl+C to stop.")

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
        confs = r.boxes.conf.cpu().tolist()
        now = time.time()

        for track_id, box, conf in zip(ids, boxes, confs):
            if now - last_print.get(track_id, 0) < PRINT_INTERVAL_SEC:
                continue
            last_print[track_id] = now

            x1, y1, x2, y2 = box
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            height = y2 - y1
            print(
                f"ID:{track_id} conf:{conf:.2f} "
                f"cx:{cx:.0f} cy:{cy:.0f} box_h:{height:.0f}"
            )


if __name__ == "__main__":
    main()
