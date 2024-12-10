import toml
import svgwrite
import random
from typing import List


class Room:
    def __init__(self, name: str, walls: List[List[float]]):
        self.name = name
        self.walls = walls
    
    def is_point_in_room(self, x: float, y: float) -> bool:
        """点が部屋のポリゴン内部にあるかを判定(Crossing Number Algorithm)"""
        n = len(self.walls)
        cross_count = 0

        for i in range(n):
            x0, y0 = self.walls[i]
            x1, y1 = self.walls[(i + 1) % n]  # 次の頂点を取得（閉じたポリゴン）

            # エッジがy座標を横断しているかを確認
            if (y0 <= y < y1) or (y1 <= y < y0):
                if x1 != x0:
                    a = (y1 - y0) / (x1 - x0)  # 傾き
                    b = y0 - a * x0  # 切片
                    intersection_x = (y - b) / a
                else:
                    intersection_x = x0  # 垂直なエッジの場合

                if x < intersection_x:
                    cross_count += 1

        return cross_count % 2 == 1

    def __repr__(self):
        return f"Room(name={self.name}, walls={self.walls})"


class Device:
    def __init__(self, mac_address: str, position: List[float]):
        self.mac_address = mac_address
        self.position = position

    def __repr__(self):
        return f"Device(mac_address={self.mac_address}, position={self.position})"


class BLEReceiver:
    def __init__(self, device_id: int, position: List[float]):
        self.device_id = device_id
        self.position = position

    def __repr__(self):
        return f"BLEReceiver(device_id={self.device_id}, position={self.position})"


class CalibrationDevice:
    def __init__(self, device_id: int, position: List[float]):
        self.device_id = device_id
        self.position = position

    def __repr__(self):
        return f"CalibrationDevice(device_id={self.device_id}, position={self.position})"



class Building:
    def __init__(self, walls: List[List[float]], rooms: List[Room]):
        self.walls = walls
        self.rooms = rooms
        self.devices = []
        self.ble_receivers = []
        self.calibration_devices = []
    
    def __repr__(self):
        return f"Building(walls={self.walls}, rooms={self.rooms}, devices={self.devices}, receivers={self.receivers})"

    def add_device(self, device: Device):
        self.devices.append(device)

    def add_calibration_device(self, calibration_device: CalibrationDevice):
        self.calibration_devices.append(calibration_device)

    def add_ble_receiver(self, ble_receiver: BLEReceiver):
        self.ble_receivers.append(ble_receiver)
    
    def bounding_box(self):
        """部屋の外接矩形を返す"""
        min_x = min([x for x, _ in self.walls])
        max_x = max([x for x, _ in self.walls])
        min_y = min([y for _, y in self.walls])
        max_y = max([y for _, y in self.walls])
        return (min_x, min_y, max_x, max_y)

    # ToDo: 美しくない...
    def _invert_coordinates(self):
        max_y_original = max([y for _, y in self.walls])
        for i, (x, y) in enumerate(self.walls):
            self.walls[i] = (x, -y + max_y_original)
        for room in self.rooms:
            for i, (x, y) in enumerate(room.walls):
                room.walls[i] = (x, -y + max_y_original)
        for device in self.devices:
            device.position = (device.position[0], -device.position[1] + max_y_original)
        for ble_receiver in self.ble_receivers:
            ble_receiver.position = (
                ble_receiver.position[0],
                -ble_receiver.position[1] + max_y_original,
            )
        for calibration_device in self.calibration_devices:
            calibration_device.position = (
                calibration_device.position[0],
                -calibration_device.position[1] + max_y_original,
            )
            

    # ToDo: 美しくない...
    def _scale_coordinates(self, scale_factor):
        for i, (x, y) in enumerate(self.walls):
            self.walls[i] = (x * scale_factor, y * scale_factor)
        for room in self.rooms:
            for i, (x, y) in enumerate(room.walls):
                room.walls[i] = (x * scale_factor, y * scale_factor)
        for device in self.devices:
            device.position = (
                device.position[0] * scale_factor,
                device.position[1] * scale_factor,
            )
        for ble_receiver in self.ble_receivers:
            ble_receiver.position = (
                ble_receiver.position[0] * scale_factor,
                ble_receiver.position[1] * scale_factor,
            )
        for calibration_device in self.calibration_devices:
            calibration_device.position = (
                calibration_device.position[0] * scale_factor,
                calibration_device.position[1] * scale_factor,
            )

    def to_svg(self, filename: str) -> str:
        # SVGのサイズ設定
        scale_factor = 8  # 拡大倍率

        self._invert_coordinates()
        self._scale_coordinates(scale_factor)  # ToDo: 反転しないデータ形式の場合の対処

        max_x = max([x for x, _ in self.walls])
        max_y = max([y for _, y in self.walls])

        # SVGのビュー設定を追加
        dwg = svgwrite.Drawing(
            filename,
            profile="tiny",
            viewBox=f"0 0 {max_x} {max_y}",
            size=(f"{max_x}px", f"{max_y}px"),
        )

        # 建物の描画
        dwg.add(
            dwg.polygon(points=self.walls, fill="gray", stroke="black", stroke_width=1)
        )

        # 部屋の描画
        for room in self.rooms:
            room_wall_points = room.walls
            dwg.add(dwg.polygon(points=room_wall_points, fill="white"))

        for room in self.rooms:
            room_wall_points = room.walls
            dwg.add(
                dwg.polygon(
                    points=room_wall_points,
                    fill="none",
                    stroke="black",
                    stroke_width=1,
                )
            )

        # デバイスの描画
        for device in self.devices:
            dwg.add(
                dwg.circle(
                    center=device.position,
                    r=2,
                    fill="red",
                    stroke="black",
                    stroke_width=0.5,
                )
            )

        # BLE受信機の描画
        for ble_receiver in self.ble_receivers:
            dwg.add(
                dwg.circle(
                    center=ble_receiver.position,
                    r=2,
                    fill="blue",
                    stroke="black",
                    stroke_width=0.5,
                )
            )
        
        # キャリブレーションデバイスの描画
        for calibration_device in self.calibration_devices:
            dwg.add(
                dwg.circle(
                    center=calibration_device.position,
                    r=2,
                    fill="green",
                    stroke="black",
                    stroke_width=0.5,
                )
            )

        return dwg.tostring()


def spawn_calibrationdevice_in_room(building: Building) -> CalibrationDevice:
    x_min, y_min, x_max, y_max = building.bounding_box()
    
    while True:
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        for room in building.rooms:
            if room.is_point_in_room(x, y):
                calibration_device = CalibrationDevice(device_id=0, position=[x, y]) # idは適当
                return calibration_device


def load_building_from_toml(file_path: str) -> Building:
    """TOMLファイルからビルディング情報を読み込む"""
    with open(file_path, "r") as file:
        data = toml.load(file)

    walls = [[float(x), float(y)] for x, y in data["building"]["walls"]]
    rooms = [
        Room(name=r["name"], walls=[[float(x), float(y)] for x, y in r["walls"]])
        for r in data["building"]["room"]
    ]
    b = Building(walls=walls, rooms=rooms)
    
    # ToDo: 追加情報を別途読み込む
    b.add_ble_receiver(BLEReceiver(device_id=1, position=[1, 1]))
    b.add_device(Device(mac_address="", position=[11, 11]))
    b.add_calibration_device(spawn_calibrationdevice_in_room(b))
    return b
