import json
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta, timezone
import os

app = Flask(__name__)

device_data = {}  # デバイスデータの辞書
receiver_positions = {}  # 受信用デバイスの位置データの辞書

# ファイルパス設定
RECEIVER_POSITIONS_FILE = 'receiver_positions.json'

# RSSIのしきい値と時間設定
RSSI_THRESHOLD = -200
SCAN_TIMEOUT = timedelta(minutes=30)
VALID_DEVICE_CHECK_PERIOD = timedelta(minutes=5)

# サーバー起動時に受信用デバイスの位置をファイルから読み込み
def load_receiver_positions():
    if os.path.exists(RECEIVER_POSITIONS_FILE):
        with open(RECEIVER_POSITIONS_FILE, 'r') as f:
            global receiver_positions
            receiver_positions = json.load(f)
    else:
        receiver_positions = {}

# 受信用デバイスの位置をファイルに保存
def save_receiver_positions():
    with open(RECEIVER_POSITIONS_FILE, 'w') as f:
        json.dump(receiver_positions, f)

# サーバー起動時にデバイスの位置を読み込み
load_receiver_positions()

# POSTされたJSONデータを受け取るエンドポイント
@app.route("/", methods=["POST"])
def post_json():
    if request.is_json:
        data = request.get_json()
        device_id = data.get("device_id")
        address = data.get("address")
        rssi = data.get("rssi")
        manufacture_id = data.get("manufacture_id")
        name = data.get("name")
        time_str = data.get("time")

        print(device_id, address, rssi, manufacture_id, name, time_str)
        try:
            timestamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid time format"}), 400

        if address and rssi is not None and device_id:
            device_data[address] = (timestamp, rssi, device_id, manufacture_id, name)
            cleanup_old_data()
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "Missing data"}), 400
    else:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

# 古いデバイスデータを削除する
def cleanup_old_data():
    cutoff_time = datetime.now(tz=timezone.utc) - SCAN_TIMEOUT
    for address in list(device_data.keys()):
        timestamp = device_data[address][0]
        if timestamp < cutoff_time:
            del device_data[address]

# 受信用デバイスの位置を保存する
@app.route("/save_devices", methods=["POST"])
def save_devices():
    if request.is_json:
        data = request.get_json()
        for device in data.get("devices", []):
            device_id = device.get("device_id")
            position = device.get("position")
            if device_id and position:
                receiver_positions[device_id] = position
        save_receiver_positions()  # ファイルに保存
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

# デバイスの位置を返す
@app.route("/get_device_positions", methods=["GET"])
def get_device_positions():
    sender_position = {"device_id": "sender1", "position": {"x": 0.5, "y": 0.5}}
    return jsonify({
        "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()],
        "sender": sender_position
    })

# 受信用デバイスの位置を返すエンドポイント
@app.route("/get_devices", methods=["GET"])
def get_devices():
    return jsonify({"devices": [{"device_id": k, "position": v} for k, v in receiver_positions.items()]})

# 有効デバイスをチェックする
def get_valid_devices():
    cutoff_time = datetime.now(tz=timezone.utc) - VALID_DEVICE_CHECK_PERIOD
    valid_devices = set()

    # 各デバイスに対して、一定のRSSI値を満たすか確認
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if (timestamp > cutoff_time) and (rssi >= RSSI_THRESHOLD):
            valid_devices.add(address)

    return valid_devices

# 有効デバイス数を表示するエンドポイント
@app.route("/valid_devices", methods=["GET"])
def valid_devices():
    valid_device_set = get_valid_devices()
    return jsonify({"valid_device_count": len(valid_device_set)})

# 30分以内のすべてのデバイス情報を取得する
@app.route("/scanned_devices", methods=["GET"])
def scanned_devices():
    scanned_devices = []
    cutoff_time = datetime.now(tz=timezone.utc) - SCAN_TIMEOUT
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if timestamp > cutoff_time:
            scanned_devices.append({
                "address": address, "rssi": rssi, "device_id": device_id,
                "manufacture_id": manufacture_id, "name": name,
                "time": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })
    return jsonify(scanned_devices)

# ユーザー用ページ
@app.route("/")
def index():
    return render_template("index.html")

# 管理者用ダッシュボード
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# 受信用デバイスの位置を設定する管理画面
@app.route("/setup")
def setup():
    return render_template("setup.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
