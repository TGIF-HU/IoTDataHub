from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
from datetime import timezone

app = Flask(__name__)

# デバイスのデータを保存する辞書 {address: [(timestamp, rssi, device_id, manufacture_id, name)]}
device_data = {}

# RSSIのしきい値と時間設定
RSSI_THRESHOLD = -200  # RSSIのしきい値（適宜調整可能）
SCAN_TIMEOUT = timedelta(minutes=30)  # 30分以上スキャンされていないデバイスを削除
VALID_DEVICE_CHECK_PERIOD = timedelta(minutes=5)  # 有効デバイスの時間範囲


# POSTされたJSONデータを受け取るエンドポイント
@app.route("/", methods=["POST"])
def post_json():
    if request.is_json:
        data = request.get_json()

        # JSONから各項目を取得
        device_id = data.get("device_id")
        address = data.get("address")  # MACアドレス
        rssi = data.get("rssi")
        manufacture_id = data.get("manufacture_id")  # 製造者コード
        name = data.get("name")  # デバイスの名前
        time_str = data.get("time")  # スキャンした時刻

        print(device_id, address, rssi, manufacture_id, name, time_str)
        try:
            # ISO 8601形式の時刻をdatetimeに変換 (ミリ秒を含む形式に対応)
            timestamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid time format"}), 400

        if address and rssi is not None and device_id:
            # デバイスデータの追加（最新のスキャンデータで上書き）
            device_data[address] = (timestamp, rssi, device_id, manufacture_id, name)

            # 古いデータを削除
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
        # timestampをoffset-awareに変換
        timestamp = device_data[address][0]
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if timestamp < cutoff_time:
            del device_data[address]


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


# 30分以内のすべてのデバイス情報を取得する
@app.route("/scanned_devices", methods=["GET"])
def scanned_devices():
    # 30分以内のスキャンされたすべてのデバイス情報を返す
    scanned_devices = []
    cutoff_time = datetime.now(tz=timezone.utc) - SCAN_TIMEOUT
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if timestamp > cutoff_time:
            scanned_devices.append({"address": address, "rssi": rssi, "device_id": device_id, "manufacture_id": manufacture_id, "name": name, "time": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
    return jsonify(scanned_devices)


# 有効デバイス数を表示するエンドポイント
@app.route("/valid_devices", methods=["GET"])
def valid_devices():
    valid_devices = get_valid_devices()
    return jsonify({"valid_device_count": len(valid_devices)})


# ダッシュボードのページを返すエンドポイント
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
