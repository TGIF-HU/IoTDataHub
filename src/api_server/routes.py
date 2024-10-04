from datetime import datetime, timedelta, timezone

from flask import jsonify, render_template, request
from utils import (
    cleanup_old_data,
    device_data,
    get_valid_devices,
    group_rssi_data_by_mac_address,
    receiver_positions,
    save_receiver_positions_to_file,
    update_sender_positions,
)


def register_routes(app):
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
            
            # timestampがあまりにも古い(１年以上)場合は、現在の時刻に設定
            if timestamp < datetime.now(tz=timezone.utc) - timedelta(days=365):
                timestamp = datetime.now(tz=timezone.utc)

            if address and rssi is not None and device_id:
                # デバイスデータを保存
                # デバイスが初めてスキャンされた場合は新しいエントリを作成
                if address not in device_data:
                    device_data[address] = {
                        "name": name,
                        "manufacture_id": manufacture_id,
                        "last_seen": timestamp,
                        "rssi_data": {
                            device_id: {
                                "rssi": rssi,
                                "timestamp": timestamp
                            }
                        }
                    }
                # すでにスキャンされたデバイスの場合はRSSIデータを追加/更新
                else:
                    device_data[address]["rssi_data"][device_id] = {
                        "rssi": rssi,
                        "timestamp": timestamp
                    }
                    device_data[address]["last_seen"] = max(timestamp, device_data[address]["last_seen"])
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
    @app.route("/save_receiver_positions", methods=["POST"])
    def save_receiver_positions():
        if request.is_json:
            data = request.get_json()
            for device in data.get("devices", []):
                device_id = device.get("device_id")
                position = device.get("position")
                if device_id and position:
                    receiver_positions[device_id] = position
            save_receiver_positions_to_file()  # ファイルに保存
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    # デバイスの位置のみを返す
    @app.route("/get_device_positions_and_receiver_positions", methods=["GET"])
    def get_device_positions_and_receiver_positions():
        sender_positions = update_sender_positions()
        return jsonify({
            "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()],
            "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
        })
    
    # TODO: JSON形式の設計
    @app.route("/get_device_positions", methods=["GET"])
    def get_device_positions():
        sender_positions = update_sender_positions()
        return jsonify({
            "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
        })
    
    # TODO: JSON形式の設計
    @app.route("/get_receiver_positions", methods=["GET"])
    def get_receiver_positions():
        return jsonify({
            "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()]
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
        return jsonify(device_data)


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