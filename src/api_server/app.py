from flask import Flask, render_template_string, jsonify
import paho.mqtt.client as mqtt
import os

app = Flask(__name__)

# MQTT ブローカー情報
MQTT_BROKER = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = 'test/topic'

# 受信したメッセージの最新値（共有する変数）
latest_message = {'value': None}

# MQTTクライアントのコールバック関数
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)  # トピックを購読

def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")
    latest_message['value'] = msg.payload.decode()  # メッセージの内容を最新の値に保存

# MQTTクライアントを設定して接続
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# MQTTの処理を別スレッドで実行
mqtt_client.loop_start()

# Webページのテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MQTT メッセージの表示</title>
</head>
<body>
    <h1>MQTT メッセージの表示</h1>
    <p>最新のメッセージ: {{ message }}</p>
    <p>計算結果: {{ result }}</p>
    <button onclick="location.reload()">更新</button>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        # 受信したメッセージ（最新の値）を取得
        value = float(latest_message['value']) if latest_message['value'] else 0
        calculated_result = value * 2  # ここで計算する（例: 値を2倍にする）
    except ValueError:
        value = 0
        calculated_result = 0

    return render_template_string(HTML_TEMPLATE, message=value, result=calculated_result)

@app.route('/api/value')
def api_value():
    """API用エンドポイント。JSONで最新の値を返す"""
    return jsonify(latest_message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

