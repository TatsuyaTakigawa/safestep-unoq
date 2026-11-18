#!/bin/bash
# One-time setup on the UNO Q (no Docker). Needs internet. Takes several minutes.
#   ./setup.sh
# Optional: IMGSZ=320 ./setup.sh   (smaller model input = faster, less accurate)
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
IMGSZ="${IMGSZ:-640}"
ULTRALYTICS_VERSION="${ULTRALYTICS_VERSION:-8.4.208}"

echo "== [1/4] apt packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip alsa-utils v4l-utils libglib2.0-0 curl

echo "== [2/4] Python virtual environment (.venv)"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip

echo "== [3/4] Python packages (CPU-only PyTorch, ultralytics, ncnn)"
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install "ultralytics==${ULTRALYTICS_VERSION}" ncnn lapx
pip uninstall -y opencv-python
pip install opencv-python-headless==5.0.0.93
python -c "import ultralytics, ncnn, lap, cv2, torch; print('deps OK', ultralytics.__version__, torch.__version__, cv2.__version__)"

echo "== [4/4] Model (NCNN)"
if [ -f models/yolo26n_ncnn_model/model.ncnn.param ]; then
    echo "NCNN model already exists. Skipped."
else
    if [ ! -f models/yolo26n.pt ]; then
        echo "Downloading yolo26n.pt (GitHub sometimes returns 504, so it retries)"
        curl -fL --retry 8 --retry-all-errors --retry-delay 5 \
            -o models/yolo26n.pt \
            https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt
    fi
    pip install pnnx
    WORK="$(mktemp -d)"
    cp models/yolo26n.pt "$WORK/"
    (cd "$WORK" && python -c "from ultralytics import YOLO; YOLO('yolo26n.pt').export(format='ncnn', imgsz=${IMGSZ})")
    rm -rf models/yolo26n_ncnn_model
    mv "$WORK/yolo26n_ncnn_model" models/
    rm -rf "$WORK"
    pip uninstall -y pnnx
fi
test -f models/yolo26n_ncnn_model/model.ncnn.param
test -f models/yolo26n_ncnn_model/model.ncnn.bin
echo
echo "Setup finished. Next: ./run.sh test-camera  /  ./run.sh test-audio  /  ./run.sh"
