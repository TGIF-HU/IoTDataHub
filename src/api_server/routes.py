from flask import Flask, request, jsonify, render_template
from device import *
# from utils import (
# cleanup_old_data,
# device_data,
# get_valid_devices,
# group_rssi_data_by_mac_address,
# receiver_positions,
# save_receiver_positions_to_file,
# update_sender_positions,
# )


class DeviceAPI(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        self.data_logger = DeviceLogger()
        self.register_routes()

    def register_routes(self):
        self.add_url_rule("/", view_func=self.index)
        # self.add_url_rule("/setup", view_func=self.setup)
        # self.add_url_rule("/dashboard", view_func=self.dashboard)

        self.add_url_rule("/api/device",
                          view_func=self.post_device, methods=["POST"])
        # self.add_url_rule("/api/valid_devices",
        #                   view_func=self.get_valid_devices, methods=["GET"])
        # self.add_url_rule("/save_receiver_positions",
        #                   view_func=self.save_receiver_positions, methods=["POST"])
        # self.add_url_rule("/get_device_positions_and_receiver_positions",
        #                   view_func=self.get_device_positions_and_receiver_positions, methods=["GET"])
        # self.add_url_rule("/get_device_positions",
        #                   view_func=self.get_device_positions, methods=["GET"])
        # self.add_url_rule("/get_receiver_positions",
        #                   view_func=self.get_receiver_positions, methods=["GET"])
        # self.add_url_rule("/get_device_rssi_admin",
        #                   view_func=self.get_device_rssi_admin, methods=["GET"])
        # self.add_url_rule("/scanned_devices",
        #                   view_func=self.scanned_devices, methods=["GET"])

    def index(self):
        return render_template("index.html")

    # def setup(self):
    #     return render_template("setup.html")

    # def dashboard(self):
    #     return render_template("dashboard.html")

    def post_device(self):
        try:
            data = DeviceData(request)
        except NotJsonException as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except JsonElementNotFoundException as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

        # すでにスキャンされたデバイスの場合はRSSIデータを追加/更新
        for d in self.data_logger:
            if d == data:  # デバイスが一致(__eq__)
                print(self.data_logger.to_dict())
                d.update(data)
                return jsonify({"status": "success"}), 200

        # デバイスが初めてスキャンされた場合は新しいエントリを作成
        self.data_logger.log(data)
        # TODO: cleanup_old_data() の機能を含んでいない
        print(self.data_logger.to_dict())
        return jsonify({"status": "success"}), 200

    # def get_valid_devices(self):
    #     VALID_DEVICE_CHECK_PERIOD = timedelta(minutes=5)
    #     cutoff_time = datetime.now(tz=timezone.utc) - VALID_DEVICE_CHECK_PERIOD

    #     valid_device_set = get_valid_devices()
    #     return jsonify({"valid_device_count": len(valid_device_set)})

    # def save_receiver_positions(self):
    #     if request.is_json:
    #         data = request.get_json()
    #         for device in data.get("devices", []):
    #             device_id = device.get("device_id")
    #             position = device.get("position")
    #             if device_id and position:
    #                 receiver_positions[device_id] = position
    #         save_receiver_positions_to_file()  # ファイルに保存
    #         return jsonify({"status": "success"}), 200
    #     return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    # def get_device_positions_and_receiver_positions(self):
    #     sender_positions = update_sender_positions()
    #     return jsonify({
    #         "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()],
    #         "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
    #     })

    # def get_device_positions(self):
    #     sender_positions = update_sender_positions()
    #     return jsonify({
    #         "senders": [{"mac_address": k, "position": v} for k, v in sender_positions.items()]
    #     })

    # def get_receiver_positions(self):
    #     return jsonify({
    #         "receivers": [{"device_id": k, "position": v} for k, v in receiver_positions.items()]
    #     })

    # def get_device_rssi_admin(self):
    #     grouped_data = group_rssi_data_by_mac_address()
    #     return jsonify({
    #         "rssi_data": grouped_data
    #     })

    # def scanned_devices(self):
    #     return jsonify(device_data)
