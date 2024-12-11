import math


def rssi2distance(rssi, power, N):
    """
    RSSIをもとに距離を計算する関数
    powerは送信機の発信電力。Nは環境依存の定数
    """
    return 10 ** ((power - rssi) / (10 * N))

def distance2rssi(distance, power, N):
    """RSSIをもとに距離を計算する関数"""
    return power - 10 * N * math.log10(distance)