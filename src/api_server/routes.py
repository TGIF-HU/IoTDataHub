from datetime import datetime, timezone

from flask import jsonify, render_template, request
from utils import (
    SCAN_TIMEOUT,
    cleanup_old_data,
    device_data,
    get_valid_devices,
    group_rssi_data_by_mac_address,
    receiver_positions,
    save_receiver_positions,
    update_sender_positions,
)


def register_routes(app):# POSTされたJSONデータを受け取るエンドポイント
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