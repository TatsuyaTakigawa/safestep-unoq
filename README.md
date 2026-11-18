# SafeStep AI for Arduino UNO Q (Dockerなし)

UNO Q の Linux 側（Debian）に直接インストールして動かす構成です。

```
safestep/
├── setup.sh              初回セットアップ（要ネット接続）
├── run.sh                起動・テスト
├── install-service.sh    OS起動時の自動起動（systemd）
├── models/               yolo26n.pt / NCNNモデル置き場（setup.sh が自動生成）
└── app/                  Pythonコード
```

## セットアップ（UNO Q上）
```bash
cd ~/safestep
chmod +x *.sh
./setup.sh
```
- 内容: apt パッケージ → Python 仮想環境(.venv) → CPU版PyTorch・ultralytics・ncnn → モデルのNCNN変換
- 数分〜数十分かかります。
- モデル入力サイズを小さくして軽くする場合: `IMGSZ=320 ./setup.sh`
- `yolo26n.pt` を自分で `models/` に置いておけば、ダウンロードは省略されます。
- Pi で使っていた `yolo26n_ncnn_model/` を `models/` に置けば、変換も省略されます。

## 使い方
USB ハブ経由で USB カメラと USB スピーカーを接続してください。

```bash
./run.sh test-camera     # camera_test.jpg を保存
./run.sh test-audio      # 警告音を1回鳴らす
./run.sh                 # 本番起動（Ctrl+Cで停止）
./install-service.sh     # OS起動時に自動起動
journalctl -u safestep -f   # 自動起動時のログ
```
カメラ・USB サウンドカードは自動検出します。うまくいかない場合は手動指定します。
```bash
SAFESTEP_CAMERA=2 SAFESTEP_AUDIO_DEVICE=plughw:1,0 ./run.sh
./run.sh audio-list      # サウンドカード番号の確認
```

## 設定（環境変数）
| 変数 | 既定値 | 内容 |
|---|---|---|
| `SAFESTEP_LINE_Y` | 240 | 仮想ラインの Y 座標 |
| `SAFESTEP_MARGIN` | 20 | ラインの不感帯 |
| `SAFESTEP_NORMAL_DIRECTION` | DOWN | 正しい向き（UP / DOWN）。逆はアラーム |
| `SAFESTEP_REVERSE_WINDOW_SEC` | 30 | 逆走を数える時間窓 |
| `SAFESTEP_REVERSE_THRESHOLD` | 1 | アラームを鳴らす人数 |
| `SAFESTEP_ALARM_COOLDOWN_SEC` | 0 | アラームのクールダウン |
| `SAFESTEP_GAP_SEC` | 3.0 | 音声と音声の間隔 |
| `SAFESTEP_CAMERA` | auto | auto / 番号(/dev/videoN) |
| `SAFESTEP_AUDIO_DEVICE` | auto | 例 `plughw:1,0`（再生できるUSBサウンドカードを自動検出） |
| `SAFESTEP_VOLUME` | 未設定 | 起動時にミキサーの再生音量を設定（0〜100） |
| `SAFESTEP_AUDIO_FILE` | `app/warning_audio/alert.wav` | 警告音ファイル。大きめの音は `alert_loud.wav` |

音が小さいときは、`SAFESTEP_VOLUME=100` と `SAFESTEP_AUDIO_FILE=$HOME/safestep/app/warning_audio/alert_loud.wav` を試してください。

自動起動で設定を変える場合は、`/etc/systemd/system/safestep.service` の `[Service]` に
`Environment=SAFESTEP_LINE_Y=200` のように追記し、`sudo systemctl daemon-reload && sudo systemctl restart safestep` を実行します。

設置場所ごとの調整には `./run.sh observe`（座標表示）と `./run.sh line-test`（ライン通過のみ）を使います。

## トラブルシュート
| 症状 | 確認 |
|---|---|
| `setup.sh` の torch でエラー | `python3 --version` と、エラー全文を確認 |
| 音が出ない | `./run.sh audio-list` → `SAFESTEP_AUDIO_DEVICE=plughw:N,0` |
| カメラが開けない | `ls /dev/video*`、`v4l2-ctl --list-devices` → `SAFESTEP_CAMERA=N` |
| FPS が低い | `rm -rf models/yolo26n_ncnn_model && IMGSZ=320 ./setup.sh` |
| メモリ不足(変換時) | PC で変換した `yolo26n_ncnn_model/` を `models/` にコピー |
