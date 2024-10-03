import json
import os
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy.optimize import minimize

device_data = {}  # デバイスデータの辞書
receiver_positions = {}  # 受信用デバイスの位置データの辞書

# ファイルパス設定
RECEIVER_POSITIONS_FILE = 'receiver_positions.json'

# RSSIのしきい値と時間設定
RSSI_THRESHOLD = -200
SCAN_TIMEOUT = timedelta(minutes=30)
VALID_DEVICE_CHECK_PERIOD = timedelta(minutes=5)

# サーバー起動時に受信用デバイスの位置をファイルから読み込み
def load_receiver_positions():
    if os.path.exists(RECEIVER_POSITIONS_FILE):
        with open(RECEIVER_POSITIONS_FILE, 'r') as f:
            global receiver_positions
            receiver_positions = json.load(f)
    else:
        receiver_positions = {}

# 受信用デバイスの位置をファイルに保存
def save_receiver_positions_to_file():
    with open(RECEIVER_POSITIONS_FILE, 'w') as f:
        json.dump(receiver_positions, f)

# サーバー起動時にデバイスの位置を読み込み
load_receiver_positions()

# RSSIから距離を推定
# TODO: 適切なパラメータを設定
def rssi_to_distance(rssi, tx_power=-50, plexp=2):
    # RSSIをもとに距離を計算する関数。tx_powerは送信機の発信電力。plexpは伝搬指数
    return 10 ** ((tx_power - rssi) / (10 * plexp))

# 三角測量による最尤推定法で送信デバイスの位置を推定
def estimate_sender_position(rssi_data):
    def objective_function(sender_position):
        total_error = 0
        for data in rssi_data:
            if data['device_id'] not in receiver_positions:
                print(f"Error: Device ID {data['device_id']} not found in receiver_positions.")
                continue  # スキップして他のデバイスで処理を続行
            
            receiver_position = receiver_positions[data['device_id']]
            rssi = data['rssi']
            estimated_distance = rssi_to_distance(rssi)
            
            # ユークリッド距離を計算
            actual_distance = np.linalg.norm(
                np.array([receiver_position['x'], receiver_position['y']]) - np.array(sender_position)
            )
            total_error += (actual_distance - estimated_distance) ** 2
        return total_error

    # 初期値 (0.5, 0.5) で最適化を開始
    result = minimize(objective_function, [0.5, 0.5], bounds=[(0, 1), (0, 1)])
    return result.x  # 推定された送信デバイスの座標

# デバイスごとにRSSIデータをグループ化し、位置推定を行う
def update_sender_positions():
    grouped_data = group_rssi_data_by_mac_address()
    sender_positions = {}

    for mac_address, rssi_data in grouped_data.items():
        if len(rssi_data) >= 3:  # 少なくとも3つの受信用デバイスが必要
            sender_positions[mac_address] = estimate_sender_position(rssi_data)

    return sender_positions

# MACアドレスごとにRSSIデータをグループ化
def group_rssi_data_by_mac_address():
    grouped_data = {}
    cutoff_time = datetime.now(tz=timezone.utc) - timedelta(seconds=10)  # 例えば10秒以内のデータ

    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if timestamp > cutoff_time:
            mac_address = address  # MACアドレスをキーとして使用
            if mac_address not in grouped_data:
                grouped_data[mac_address] = []
            grouped_data[mac_address].append({
                "device_id": device_id,
                "rssi": rssi,
                "name": name
            })

    return grouped_data


# 古いデバイスデータを削除する
def cleanup_old_data():
    cutoff_time = datetime.now(tz=timezone.utc) - SCAN_TIMEOUT
    for address in list(device_data.keys()):
        timestamp = device_data[address][0]
        if timestamp < cutoff_time:
            del device_data[address]

# 有効デバイスをチェックする関数を修正
def get_valid_devices():
    cutoff_time = datetime.now(tz=timezone.utc) - VALID_DEVICE_CHECK_PERIOD
    valid_devices = set()

    # 各デバイスに対して、一定のRSSI値を満たすか確認
    for address, entry in device_data.items():
        timestamp, rssi, device_id, manufacture_id, name = entry
        if (timestamp > cutoff_time) and (rssi >= RSSI_THRESHOLD):
            valid_devices.add(address)

    return valid_devices