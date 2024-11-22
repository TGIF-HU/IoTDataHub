import toml
import svgwrite
from typing import List


class Room:
    def __init__(self, name: str, walls: List[List[float]]):
        self.name = name
        self.walls = walls

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


class Building:
    def __init__(
        self,
        walls: Room,
        rooms: List[Room],
        devices: List[Device],
        receivers: List[BLEReceiver],
    ):
        self.walls = walls  # 建物の大枠の壁
        self.rooms = rooms  # 部屋のリスト
        self.devices = devices  # デバイスのリスト
        self.receivers = receivers  # BLE受信機のリスト

    def __repr__(self):
        return f"Building(walls={self.walls}, rooms={self.rooms}, devices={self.devices}, receivers={self.receivers})"

    def _invert_coordinates(self):
        max_y_original = max([y for _, y in self.walls])
        for i, (x, y) in enumerate(self.walls):
            self.walls[i] = (x, -y + max_y_original)
        for room in self.rooms:
            for i, (x, y) in enumerate(room.walls):
                room.walls[i] = (x, -y + max_y_original)
        for device in self.devices:
            device.position = (device.position[0], -device.position[1] + max_y_original)
        for receiver in self.receivers:
            receiver.position = (
                receiver.position[0],
                -receiver.position[1] + max_y_original,
            )

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
        for receiver in self.receivers:
            receiver.position = (
                receiver.position[0] * scale_factor,
                receiver.position[1] * scale_factor,
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
        room_fill_color = "white"
        for room in self.rooms:
            room_wall_points = room.walls
            dwg.add(dwg.polygon(points=room_wall_points, fill=room_fill_color))

        room_border_color = "black"
        for room in self.rooms:
            room_wall_points = room.walls
            dwg.add(
                dwg.polygon(
                    points=room_wall_points,
                    fill="none",
                    stroke=room_border_color,
                    stroke_width=1,
                )
            )

        # デバイスの描画
        device_radius = 2
        device_fill_color = "red"
        for device in self.devices:
            dwg.add(
                dwg.circle(
                    center=device.position,
                    r=device_radius,
                    fill=device_fill_color,
                    stroke="black",
                    stroke_width=0.5,
                )
            )

        # BLE受信機の描画
        receiver_radius = 2
        receiver_fill_color = "blue"
        for receiver in self.receivers:
            dwg.add(
                dwg.circle(
                    center=receiver.position,
                    r=receiver_radius,
                    fill=receiver_fill_color,
                    stroke="black",
                    stroke_width=0.5,
                )
            )

        return dwg.tostring()


# TOMLファイルからビルディング情報を読み込む
def load_building_from_toml(file_path):
    with open(file_path, "r") as file:
        data = toml.load(file)

    building_walls = [[float(x), float(y)] for x, y in data["building"]["walls"]]

    rooms = []
    for room_data in data["building"]["room"]:
        room_walls = [[float(x), float(y)] for x, y in room_data["walls"]]
        room = Room(name=room_data["name"], walls=room_walls)
        rooms.append(room)

    ble_receivers = [BLEReceiver(device_id=1, position=[1, 1])]

    devices = [
        Device(mac_address="", position=[11, 11])
    ]  # ToDo: デバイスを常に更新するように

    return Building(
        walls=building_walls, rooms=rooms, devices=devices, receivers=ble_receivers
    )
