import numpy as np
from scipy.optimize import minimize
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
RSSI_TO_DISTANCE_CONSTANT = 2  # 距離計算用の伝搬指数n

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

# RSSIから距離を推定
def rssi_to_distance(rssi, tx_power=-50):
    # RSSIをもとに距離を計算する関数。tx_powerは送信機の発信電力。
    return 10 ** ((tx_power - rssi) / (10 * RSSI_TO_DISTANCE_CONSTANT))

# 三角測量による最尤推定法で送信デバイスの位置を推定
def estimate_sender_position(rssi_data):
    def objective_function(sender_position):
        total_error = 0
        for data in rssi_data:
            if data['device_id'] not in receiver_positions:
                print(f"Error: Device ID {data['device_id']} not found in receiver_positions.")
                continue  # スキップして他のデバイスで処理を続行
            
            receiver_position = receiver_positions[data['device_id']]
            rssi = data['rssi']
            estimated_distance = rssi_to_distance(rssi)
            
            # ユークリッド距離を計算
            actual_distance = np.linalg.norm(
                np.array([receiver_position['x'], receiver_position['y']]) - np.array(sender_position)
            )
            total_error += (actual_distance - estimated_distance) ** 2
        return total_error

    # 初期値 (0.5, 0.5) で最適化を開始
    result = minimize(objective_function, [0.5, 0.5], bounds=[(0, 1), (0, 1)])
    return result.x  # 推定された送信デバイスの座標

# デバイスごとにRSSIデータをグループ化し、位置推定を行う
def update_sender_positions():
    grouped_data = group_rssi_data_by_mac_address()
    sender_positions = {}

    for mac_address, rssi_data in grouped_data.items():
        if len(rssi_data) >= 3:  # 少なくとも3つの受信用デバイスが必要
            sender_positions[mac_address] = estimate_sender_position(rssi_data)

    return sender_positions

# MACアドレスごとにRSSIデータをグループ化
def group_rssi_data_by_mac_address():
    grouped_data = {}
    cutoff_time = datetime.now(tz=timezone.utc) - timedelta(seconds=10)  # 例えば10秒以内のデータ

    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if timestamp > cutoff_time:
            mac_address = address  # MACアドレスをキーとして使用
            if mac_address not in grouped_data:
                grouped_data[mac_address] = []
            grouped_data[mac_address].append({
                "device_id": device_id,
                "rssi": rssi,
                "name": name
            })

    return grouped_data

# POSTされたJSONデータを受け取るエンドポイント
@app.route("/", methods=["POST"])
def post_json():
    if request.is_json:
        data = request.get_json()
        device_id = data.get("device_id")
        address = data.get("address")  # MACアドレス
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

# 有効デバイスをチェックする関数を修正
def get_valid_devices():
    cutoff_time = datetime.now(tz=timezone.utc) - VALID_DEVICE_CHECK_PERIOD
    valid_devices = set()

    # 各デバイスに対して、一定のRSSI値を満たすか確認
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if (timestamp > cutoff_time) and (rssi >= RSSI_THRESHOLD):
            valid_devices.add(address)

    return valid_devices

@app.route("/valid_devices", methods=["GET"])
def valid_devices():
    valid_device_set = get_valid_devices()
    return jsonify({"valid_device_count": len(valid_device_set)})


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

# デバイスの位置のみを返す
@app.route("/get_device_positions_admin", methods=["GET"])
def get_device_positions_admin():
    sender_positions = update_sender_positions()
    return jsonify({
        "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()],
        "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
    })

# RSSIデータを返すエンドポイント
@app.route("/get_device_rssi_admin", methods=["GET"])
def get_device_rssi_admin():
    grouped_data = group_rssi_data_by_mac_address()
    return jsonify({
        "rssi_data": grouped_data
    })

# 30分以内のスキャンされたすべてのデバイス情報を返す
@app.route("/scanned_devices", methods=["GET"])
def scanned_devices():
    # 30分以内のスキャンされたすべてのデバイス情報を返す
    scanned_devices = []
    cutoff_time = datetime.now(tz=timezone.utc) - SCAN_TIMEOUT
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if timestamp > cutoff_time:
            scanned_devices.append({
                "address": address,
                "rssi": rssi,
                "device_id": device_id,
                "manufacture_id": manufacture_id,
                "name": name,
                "time": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })
    return jsonify(scanned_devices)


# 受信用デバイスの位置を設定する管理画面
@app.route("/setup")
def setup():
    return render_template("setup.html")

# ユーザー用ページ
@app.route("/")
def index():
    return render_template("index.html")

# 管理者用ダッシュボード
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
