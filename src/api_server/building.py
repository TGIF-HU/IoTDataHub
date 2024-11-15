import toml
import svgwrite


class Room:
    def __init__(self, name, walls):
        self.name = name
        self.walls = walls

    def __repr__(self):
        return f"Room(name={self.name}, walls={self.walls})"


class Building:
    def __init__(self, walls, rooms):
        self.walls = walls  # 建物の大枠の壁
        self.rooms = rooms  # 部屋のリスト

    def add_room(self, room):
        self.rooms.append(room)

    def __repr__(self):
        return f"Building(walls={self.walls}, rooms={self.rooms})"

    def _invert_coordinates(self):
        max_y_original = max([y for _, y in self.walls])
        for i, (x, y) in enumerate(self.walls):
            self.walls[i] = (x, -y + max_y_original)
        for room in self.rooms:
            for i, (x, y) in enumerate(room.walls):
                room.walls[i] = (x, -y + max_y_original)

    def _scale_coordinates(self, scale_factor):
        for i, (x, y) in enumerate(self.walls):
            self.walls[i] = (x * scale_factor, y * scale_factor)
        for room in self.rooms:
            for i, (x, y) in enumerate(room.walls):
                room.walls[i] = (x * scale_factor, y * scale_factor)

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

    return Building(walls=building_walls, rooms=rooms)
