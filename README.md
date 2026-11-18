# SafeStep AI for Arduino UNO Q

**階段・通路での人の逆方向通行を検知し、音で注意を促すエッジAI試作システム**です。USBカメラの映像をArduino UNO Q上で処理し、人物の追跡と仮想ラインの通過方向判定を行います。逆方向の通過を検知すると、接続したスピーカーから警告音を再生します。

> **安全に関する注意**：本ソフトウェアはコンテスト向けの試作です。検知漏れ・誤検知があり得るため、人の安全を保証する装置や、法令上必要な安全設備の代替として使用しないでください。実環境に設置する前に、十分な検証と監視を行ってください。

## 特長

- Arduino UNO QのLinux環境上で動作
- YOLO26nによる人物検出とトラッキング
- 画面上の仮想ラインを基準に通過方向を判定
- 逆方向通過を時間窓内で集計し、しきい値に応じて警告音を再生
- USBカメラと再生可能なUSBオーディオデバイスを自動検出
- ライン位置、通行方向、警報条件などを環境変数で調整可能
- systemdによる起動時の自動実行に対応

## 動作のしくみ

1. USBカメラから映像を取得します。
2. YOLO26nで人物を検出し、フレーム間で同一人物を追跡します。
3. 人物のバウンディングボックス中心が仮想ラインを横切ったかを判定します。
4. 設定した通常方向と逆向きの通過を記録します。
5. 指定時間内の逆方向通過数がしきい値に達すると、警告音を再生します。

判定ラインは画像のY座標で指定します。カメラの向きや設置位置が変わると、ライン位置と通常方向の再調整が必要です。

## リポジトリ構成

```text
.
├── setup.sh                 初回セットアップとモデル準備
├── run.sh                   起動、テスト、調整用コマンド
├── install-service.sh       systemdサービスの登録・削除
├── app/
│   ├── safestep_run.py      人物追跡・通過方向判定
│   ├── safestep_config.py   設定とデバイス検出
│   ├── alarm_player.py      警告音再生
│   ├── camera_test.py       カメラ確認
│   ├── observe.py           追跡位置の確認
│   ├── line_test.py         ライン通過確認
│   └── warning_audio/       警告音ファイル
└── models/                  モデル保存先（セットアップ時に準備）
```

## 必要なもの

- Arduino UNO Q（Linux側で本リポジトリを実行）
- USBカメラ
- 音声出力機器（USBスピーカー、またはUSBオーディオアダプターとスピーカー）
- 初回セットアップ時のインターネット接続
- Python 3と`sudo`が利用できる環境

USB機器の認識状況は接続方法や機器によって異なります。カメラとオーディオ機器は、初回起動前に個別にテストしてください。

## セットアップ

UNO Q上でリポジトリのディレクトリに移動して実行します。

```bash
chmod +x ./*.sh
./setup.sh
```

`setup.sh`は必要なOSパッケージ、Python仮想環境（`.venv`）、CPU版PyTorch、Ultralytics、NCNN関連パッケージを準備し、YOLO26nモデルをNCNN形式に変換します。初回はパッケージとモデルのダウンロードおよび変換に時間がかかります。

既定の入力サイズは640です。処理負荷を下げたい場合は、精度とのトレードオフを確認しながら入力サイズを小さくしてセットアップします。

```bash
IMGSZ=320 ./setup.sh
```

変換済みモデルは`models/yolo26n_ncnn_model/`に置かれます。セットアップスクリプトは、そこに必要なNCNNファイルがすでにある場合はモデル変換をスキップします。

## 起動と動作確認

USBカメラと音声出力機器を接続した状態で、次のコマンドを実行します。

```bash
./run.sh test-camera   # カメラ画像を取得し、camera_test.jpgを保存
./run.sh test-audio    # 警告音を1回再生
./run.sh audio-list    # ALSAサウンドカード一覧を表示
./run.sh observe       # 追跡位置を表示し、ライン位置調整に使用
./run.sh line-test     # ライン通過判定を確認
./run.sh               # 検知と警告音再生を開始（Ctrl+Cで停止）
```

### 設置・判定の調整

1. `./run.sh test-camera`で、カメラ映像が取得できることを確認します。
2. `./run.sh observe`を実行し、対象者の位置と画面上のY座標を確認します。
3. `SAFESTEP_LINE_Y`で、通行者が通過する位置に仮想ラインを設定します。
4. `SAFESTEP_NORMAL_DIRECTION`で通常の通行方向を指定します。
5. `./run.sh line-test`で、ライン通過の向きが想定どおりか確認します。
6. `./run.sh test-audio`で警告音の出力先と音量を確認し、本番起動します。

例：ラインをY=200に設定し、画面上方向への通過を通常とする場合。

```bash
SAFESTEP_LINE_Y=200 SAFESTEP_NORMAL_DIRECTION=UP ./run.sh
```

## 設定項目

設定は環境変数で上書きできます。既定値は現在のコードに基づきます。

| 環境変数 | 既定値 | 説明 |
|---|---:|---|
| `SAFESTEP_LINE_Y` | `240` | 仮想ラインのY座標 |
| `SAFESTEP_MARGIN` | `20` | ライン付近の判定除外幅（不感帯） |
| `SAFESTEP_NORMAL_DIRECTION` | `DOWN` | 通常方向。`UP`または`DOWN` |
| `SAFESTEP_REVERSE_WINDOW_SEC` | `30` | 逆方向通過を集計する時間窓（秒） |
| `SAFESTEP_REVERSE_THRESHOLD` | `1` | 警報を発する逆方向通過人数のしきい値 |
| `SAFESTEP_ALARM_COOLDOWN_SEC` | `0` | 警報後のクールダウン時間（秒） |
| `SAFESTEP_GAP_SEC` | `3.0` | 警告音再生後、次の再生までの間隔（秒） |
| `SAFESTEP_CAMERA` | `auto` | カメラ指定。`auto`、デバイス番号（例：`2`）、パスまたはURL |
| `SAFESTEP_AUDIO_DEVICE` | 自動検出 | ALSAデバイス（例：`plughw:1,0`）。空の場合はUSBオーディオを検出し、なければ既定デバイスを使用 |
| `SAFESTEP_VOLUME` | 未設定 | 起動時のミキサー音量（`0`〜`100`）。未設定の場合は変更しない |
| `SAFESTEP_AUDIO_FILE` | `app/warning_audio/alert.wav` | 再生するWAVファイル |
| `SAFESTEP_MODEL` | `models/yolo26n_ncnn_model` | 使用するモデルのパス |

警告音を大きくしたい場合は、まず接続先やミキサー設定を確認してください。必要に応じて、同梱ファイルの存在を確認したうえで、次のように指定できます。

```bash
SAFESTEP_VOLUME=100 \
SAFESTEP_AUDIO_FILE="$PWD/app/warning_audio/alert_loud.wav" \
./run.sh
```

デバイスを明示して起動する例：

```bash
SAFESTEP_CAMERA=2 SAFESTEP_AUDIO_DEVICE=plughw:1,0 ./run.sh
```

## systemdで自動起動

セットアップ完了後に実行します。

```bash
./install-service.sh
```

ログの確認とサービス停止は次のとおりです。

```bash
journalctl -u safestep -f
sudo systemctl stop safestep
```

自動起動時の設定を変える場合は、`/etc/systemd/system/safestep.service`の`[Service]`セクションに、たとえば次の行を追加します。

```ini
Environment=SAFESTEP_LINE_Y=200
Environment=SAFESTEP_NORMAL_DIRECTION=UP
```

変更後にサービスを再読み込みして再起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl restart safestep
```

サービスを削除する場合：

```bash
./install-service.sh remove
```

## テスト環境

以下の構成で動作確認を行いました。

| 項目 | 確認した環境 |
|---|---|
| ボード | Arduino UNO Q |
| デバイスツリーモデル | Arduino UnoQ |
| CPU | Kryo-V2 × 4 |
| RAM | 3.6 GB |
| ルートストレージ | 20 GB |
| OS | Debian GNU/Linux 13 (trixie) |
| Kernel | `7.0.0-g122c2c22d838`（aarch64） |
| Python | 3.13.5（venv使用） |
| Ultralytics | 8.4.208 |
| PyTorch | 2.15.0+cpu |
| torchvision | 0.29.2+cpu |
| NCNN | 1.0.20261020 |
| OpenCV | opencv-python-headless 5.0.0.93 |
| lapx | 0.13.1 |
| NumPy | 2.5.4 |
| ALSA utils | 1.2.14 |
| systemd | 257 |
| Git | 2.47.3 |
| 使用モデル | YOLO26n（NCNN形式） |

### 接続機器の例

- Logitech Webcam C270（USBカメラ）
- Jieli Technology UACDemoV1.0（USBオーディオ）
- Arduino-Imola-HPH-LOUT（ボード上の音声デバイス）
- Genesys Logic USBハブ

接続機器の識別情報は実験時の一例です。環境によってデバイス番号やALSAカード番号は変わります。

## トラブルシューティング

| 症状 | 確認・対処 |
|---|---|
| カメラを開けない | `ls /dev/video*`でデバイスを確認し、`./run.sh test-camera`を実行。必要なら`SAFESTEP_CAMERA=N`で番号を指定 |
| 別のカメラや内部デバイスが選ばれる | `SAFESTEP_CAMERA=N`でUSBカメラのデバイス番号を明示 |
| 音が出ない | `./run.sh audio-list`でALSAカードを確認し、`SAFESTEP_AUDIO_DEVICE=plughw:N,0`を指定して`./run.sh test-audio`を実行 |
| 警報音が小さい | ミキサーと接続先を確認し、`SAFESTEP_VOLUME=100`や別の警告音ファイルを試す |
| セットアップ中にPyTorch関連のエラー | `python3 --version`とエラー全文を確認。UNO Q上で利用できるPython/CPU向けwheelか確認 |
| 推論が遅い | `IMGSZ=320 ./setup.sh`でモデルを再作成し、精度と速度を実環境で比較 |
| モデル変換時にメモリ不足 | 対応環境で作成したNCNNモデルを`models/yolo26n_ncnn_model/`に配置してからセットアップを再実行 |
| 自動起動しない | `systemctl status safestep`と`journalctl -u safestep`でログを確認 |

## 制約

- カメラの画角、設置高さ、照明、混雑、遮蔽、歩行速度などにより検知性能が変化します。
- 人物トラッキングIDは映像状況によって途切れたり入れ替わったりする可能性があります。
- 警告音の聞こえ方はスピーカー、設置環境、周囲の騒音に依存します。
