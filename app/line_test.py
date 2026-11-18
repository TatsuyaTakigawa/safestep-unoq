import safestep_config as cfg

model = cfg.load_model()
previous_side = {}

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
                print(
                    f"ID:{track_id} LINE CROSS "
                    f"{old_side} -> {side} "
                    f"cy:{cy:.1f}"
                )

        previous_side[track_id] = side
