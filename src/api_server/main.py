from flask import Flask, request, jsonify, render_template, Response
from device import *
from building import load_building_from_toml

MAP_FILE = "cafeteria.toml"
OUTPUT_FILE = "cafeteria.svg"

app = Flask(__name__)

data_logger = DeviceLogger()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/histgram")
def histgram():
    return render_template("histgram.html")


@app.route("/scanned_devices")
def scanned_devices():
    return render_template("scanned_devices.html")


@app.route("/devices_map")
def devices_map():
    return render_template("devices_map.html")


# API関連
@app.route("/api/device", methods=["POST"])
def post_device():
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
    for d in data_logger:
        if d == data:  # デバイスが一致(__eq__)
            d.update(data)
            return jsonify({"status": "success"}), 200

    # デバイスが初めてスキャンされた場合は新しいエントリを作成
    data_logger.log(data)
    # 古いデータを削除
    data_logger.cleanup_old_data()
    return jsonify({"status": "success"}), 200


@app.route("/api/scanned_devices", methods=["GET"])
def get_scanned_devices():
    return jsonify(data_logger.to_dict())


@app.route("/api/valid_devices", methods=["GET"])
def get_valid_devices():
    return jsonify({"valid_device_count": data_logger.valid_devices_length()})


@app.route("/api/rssi", methods=["GET"])
def get_rssi():
    # 出力例:
    # curl -X GET  http://192.168.2.105:5050/api/rssi
    # {"1":[-79,-83,-95,-89,-73,-95,-72,-81,-88,-94,-96,-100,-96,-76,-99,-98]}
    device_ids = []
    rssi_data = {}
    for d in data_logger:
        if d.device_id not in device_ids:
            device_ids.append(d.device_id)
            rssi_data[d.device_id] = [d.rssi]
        else:
            rssi_data[d.device_id].append(d.rssi)
    return jsonify(rssi_data)


@app.route("/api/devices_map", methods=["GET"])
def get_devices_map():
    building = load_building_from_toml(MAP_FILE)
    svg_data = building.to_svg(OUTPUT_FILE)
    print(svg_data)
    return Response(svg_data, mimetype="image/svg+xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
