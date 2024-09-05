from flask import Flask, request, jsonify

app = Flask(__name__)

# POSTされたJSONデータを受け取ってprintするエンドポイント


@app.route('/', methods=['POST'])
def post_json():
    if request.is_json:
        # JSONデータを取得
        data = request.get_json()

        # 受け取ったデータをprint
        print("Received JSON data:")
        print(data)

        # レスポンスとして受け取ったデータを返す
        return jsonify({"status": "success", "received_data": data}), 200
    else:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
