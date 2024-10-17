from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta, timezone
from utils import (
    cleanup_old_data,
    device_data,
    get_valid_devices,
    group_rssi_data_by_mac_address,
    receiver_positions,
    save_receiver_positions_to_file,
    update_sender_positions,
)

class DeviceData:
    def __init__(self, json_data):
        self.device_id = json_data.get("device_id")
        self.address = json_data.get("address")
        self.rssi = json_data.get("rssi")
        self.manufacture_id = json_data.get("manufacture_id")
        self.name = json_data.get("name")
        self.time_str = json_data.get("time")
        self.timestamp = self.parse_timestamp(self.time_str)

    def parse_timestamp(self, time_str):
        try:
            return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

    def is_valid(self):
        return self.device_id is not None and self.address is not None and self.rssi is not None and self.timestamp is not None

    def to_dict(self):
        return {
            "name": self.name,
            "manufacture_id": self.manufacture_id,
            "last_seen": self.timestamp,
            "rssi_data": {
                self.device_id: {
                    "rssi": self.rssi,
                    "timestamp": self.timestamp
                }
            }
        }

class DeviceAPI(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        self.register_routes()

    def register_routes(self):
        self.add_url_rule("/", view_func=self.post_json, methods=["POST"])
        self.add_url_rule("/valid_devices", view_func=self.valid_devices, methods=["GET"])
        self.add_url_rule("/save_receiver_positions", view_func=self.save_receiver_positions, methods=["POST"])
        self.add_url_rule("/get_device_positions_and_receiver_positions", view_func=self.get_device_positions_and_receiver_positions, methods=["GET"])
        self.add_url_rule("/get_device_positions", view_func=self.get_device_positions, methods=["GET"])
        self.add_url_rule("/get_receiver_positions", view_func=self.get_receiver_positions, methods=["GET"])
        self.add_url_rule("/get_device_rssi_admin", view_func=self.get_device_rssi_admin, methods=["GET"])
        self.add_url_rule("/scanned_devices", view_func=self.scanned_devices, methods=["GET"])
        
        self.add_url_rule("/", view_func=self.index)
        self.add_url_rule("/setup", view_func=self.setup)
        self.add_url_rule("/dashboard", view_func=self.dashboard)

    def post_json(self):
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

        data = DeviceData(request.get_json())
        if not data.is_valid():
            return jsonify({"status": "error", "message": "Invalid or missing data"}), 400

        # timestampがあまりにも古い(１年以上)場合は、現在の時刻に設定
        if data.timestamp < datetime.now(tz=timezone.utc) - timedelta(days=365):
            data.timestamp = datetime.now(tz=timezone.utc)

        if data.address not in device_data:
            # デバイスが初めてスキャンされた場合は新しいエントリを作成
            device_data[data.address] = data.to_dict()
        else:
            # すでにスキャンされたデバイスの場合はRSSIデータを追加/更新
            device_data[data.address]["rssi_data"][data.device_id] = {
                "rssi": data.rssi,
                "timestamp": data.timestamp
            }
            device_data[data.address]["last_seen"] = max(data.timestamp, device_data[data.address]["last_seen"])

        cleanup_old_data()
        return jsonify({"status": "success"}), 200

    def valid_devices(self):
        valid_device_set = get_valid_devices()
        return jsonify({"valid_device_count": len(valid_device_set)})

    def save_receiver_positions(self):
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

    def get_device_positions_and_receiver_positions(self):
        sender_positions = update_sender_positions()
        return jsonify({
            "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()],
            "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
        })

    def get_device_positions(self):
        sender_positions = update_sender_positions()
        return jsonify({
            "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
        })

    def get_receiver_positions(self):
        return jsonify({
            "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()]
        })

    def get_device_rssi_admin(self):
        grouped_data = group_rssi_data_by_mac_address()
        return jsonify({
            "rssi_data": grouped_data
        })

    def scanned_devices(self):
        return jsonify(device_data)

    def setup(self):
        return render_template("setup.html")

    def index(self):
        return render_template("index.html")

    def dashboard(self):
        return render_template("dashboard.html")