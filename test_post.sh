curl -X POST http://127.0.0.1:5000/ \
-H "Content-Type: application/json" \
-d '{
    "device_id": "12345",
    "address": "00:11:22:33:44:55",
    "rssi": -67,
    "manufacture_id": 1234,
    "name": "TestDevice",
    "time": "2024-09-05T12:34:56Z"
}'