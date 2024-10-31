import toml

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


# Load data from TOML file
def load_building_from_toml(file_path):
    with open(file_path, 'r') as file:
        data = toml.load(file)

    building_walls = data['building']['walls']
    rooms = []
    for room_data in data['building']['room']:
        room = Room(name=room_data['name'], walls=room_data['walls'])
        rooms.append(room)

    return Building(walls=building_walls, rooms=rooms)


# Create the building and rooms based on the TOML file
building = load_building_from_toml('cafeteria.toml')

# Print the building representation
print(building)
