from flask import Flask, request, jsonify, render_template, Response
from device import *
from building import load_building_from_toml

MAP_FILE = 'cafeteria.toml'
OUTPUT_FILE = 'cafeteria.svg'

class DeviceAPI(Flask):
    def __init__(self, import_name):
        super().__init__(import_name)
        self.data_logger = DeviceLogger()
        self.register_routes()

    def register_routes(self):
        self.add_url_rule("/", view_func=self.index)
        self.add_url_rule("/dashboard", view_func=self.dashboard)
        self.add_url_rule("/histgram", view_func=self.histgram)
        self.add_url_rule("/scanned_devices", view_func=self.scanned_devices)

        self.add_url_rule("/api/device",
                          view_func=self.post_device, methods=["POST"])
        self.add_url_rule("/api/scanned_devices",
                          view_func=self.get_scanned_devices, methods=["GET"])
        self.add_url_rule("/api/valid_devices",
                          view_func=self.get_valid_devices, methods=["GET"])
        self.add_url_rule("/api/rssi",
                          view_func=self.get_rssi, methods=["GET"])
        self.add_url_rule("/api/devices_map",
                          view_func=self.get_devices_map, methods=["GET"])
        # self.add_url_rule("/save_receiver_positions",
        #                   view_func=self.save_receiver_positions, methods=["POST"])
        # self.add_url_rule("/get_device_positions_and_receiver_positions",
        #                   view_func=self.get_device_positions_and_receiver_positions, methods=["GET"])
        # self.add_url_rule("/get_device_positions",
        #                   view_func=self.get_device_positions, methods=["GET"])
        # self.add_url_rule("/get_receiver_positions",
        #                   view_func=self.get_receiver_positions, methods=["GET"])

    def index(self):
        return render_template("index.html")

    def dashboard(self):
        return render_template("dashboard.html")
    
    def histgram(self):
        return render_template("histgram.html")
    
    def scanned_devices(self):
        return render_template("scanned_devices.html")

    def post_device(self):
        try:
            data = DeviceData(request)
        except NotJsonException as e:
            print(e)
            return jsonify({"status": "error", "message": str(e)}), 400
        except JsonElementNotFoundException as e:
            print(e)
            return jsonify({"status": "error", "message": str(e)}), 400
        except ValueError as e:
            print(e)
            return jsonify({"status": "error", "message": str(e)}), 400

        # すでにスキャンされたデバイスの場合はRSSIデータを追加/更新
        for d in self.data_logger:
            if d == data:  # デバイスが一致(__eq__)
                d.update(data)
                return jsonify({"status": "success"}), 200

        # デバイスが初めてスキャンされた場合は新しいエントリを作成
        self.data_logger.log(data)
        # 古いデータを削除
        self.data_logger.cleanup_old_data()
        # print(self.data_logger.to_dict())
        return jsonify({"status": "success"}), 200

    def get_scanned_devices(self):
        return jsonify(self.data_logger.to_dict())

    def get_valid_devices(self):
        return jsonify({"valid_device_count": self.data_logger.valid_devices_length()})

    def get_rssi(self):
        # 出力例:
        # curl -X GET  http://192.168.2.105:5050/api/rssi
        # {"1":[-79,-83,-95,-89,-73,-95,-72,-81,-88,-94,-96,-100,-96,-76,-99,-98]}
        device_ids = []
        rssi_data = {}
        for d in self.data_logger:
            if d.device_id not in device_ids:
                device_ids.append(d.device_id)
                rssi_data[d.device_id] = [d.rssi]
            else:
                rssi_data[d.device_id].append(d.rssi)
        return jsonify(rssi_data)

    def get_devices_map(self):
        building = load_building_from_toml(MAP_FILE)
        svg_data = building.to_svg(OUTPUT_FILE)
        print(svg_data)
        return Response(svg_data, mimetype='image/svg+xml')

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
