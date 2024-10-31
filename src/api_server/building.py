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
        self.walls = walls
        self.rooms = rooms

    def add_room(self, room):
        self.rooms.append(room)

    def __repr__(self):
        return f"Building(walls={self.walls}, rooms={self.rooms})"

    def to_svg(self, filename):
        dwg = svgwrite.Drawing(filename, profile='tiny')
        max_y = max([y for _, y in self.walls])
        # Draw building
        building_wall_points = [(x, -y + max_y) for x, y in self.walls]
        dwg.add(dwg.polygon(points=building_wall_points, fill='black'))

        # Draw rooms
        colors_palette = ['red', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']
        for color, room in zip(colors_palette, self.rooms):
            room_wall_points = [(x, -y + max_y) for x, y in room.walls]
            dwg.add(dwg.polygon(points=room_wall_points, fill=color))

        dwg.save()


# TOMLファイルからビルディング情報を読み込む
def load_building_from_toml(file_path):
    with open(file_path, 'r') as file:
        data = toml.load(file)

    building_walls = [[float(x), float(y)] for x, y in data['building']['walls']]
    rooms = []
    for room_data in data['building']['room']:
        room_walls = [[float(x), float(y)] for x, y in room_data['walls']]
        room = Room(name=room_data['name'], walls=room_walls)
        rooms.append(room)

    return Building(walls=building_walls, rooms=rooms)


# SVGの生成
building = load_building_from_toml('cafeteria.toml')
building.to_svg('cafeteria.svg')