import toml


# RSSIをもとに距離を計算する関数
# powerは送信機の発信電力。Nは環境依存の定数
def rssi2distance(rssi, power, N):
    return 10 ** ((power - rssi) / (10 * N))
