from threading import Timer
import sqlite3
from device import DeviceData
from typing import List


# ble_calibraion.rsの保存するデータのクラス
class CalibrationData:
    def from_devicedata(self, data: DeviceData, place: str, position: List[float]):
        self.device_id = data.device_id
        self.rssi = data.rssi
        self.timestamp = data.timestamp
        self.place = place
        self.position = position

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.name == other.name) and (self.timestamp == other.timestamp)
        else:
            raise ValueError("Invalid data type")
    
    def __repr__(self) -> str:
        return f"CalibrationData(device_id={self.device_id}, rssi={self.rssi}, timestamp={self.timestamp}, place={self.place}, position={self.position})"

class DatabaseManeger:
    def __init__(self, db_file):
        self.db_file = db_file
        
        # List型がないので、sqlite3に登録
        sqlite3.register_adapter(list, lambda l: ';'.join([str(i) for i in l]))
        sqlite3.register_converter('List', lambda s: [item.decode('utf-8')  for item in s.split(bytes(b';'))])
        
        db = sqlite3.connect(self.db_file)
        cursor = db.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS device_data ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "device_id INTEGER,"
            "rssi INTEGER,"
            "timestamp TEXT,"
            "place TEXT,"
            "position List"
            ")"
        )
        db.commit()
        db.close()

    def save(self, data: CalibrationData):
        print("Saving CalibrationData...")
        db = sqlite3.connect(self.db_file)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO device_data (device_id, rssi, timestamp, place, position) VALUES (?, ?, ?, ?, ?)",
            (data.device_id, data.rssi, data.timestamp, data.place, data.position),
        )
        db.commit()
        db.close()
