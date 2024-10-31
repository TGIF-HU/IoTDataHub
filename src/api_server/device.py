from datetime import datetime, timedelta, timezone


class DeviceData:
    def __init__(self, request):
        if not request.is_json:
            raise NotJsonException

        json_data = request.get_json()
        self.device_id = json_data.get("device_id")
        self.mac_address = json_data.get("address")
        self.rssi = json_data.get("rssi")
        self.manufacture_id = json_data.get("manufacture_id")
        self.name = json_data.get("name")
        time_str = json_data.get("time")
        # TODO "%Y-%m-%dT%H:%M:%SZ"か"%Y-%m-%dT%H:%M:%S.%fZ"か
        self.timestamp = datetime.strptime(
            time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

        if self.device_id is None and self.mac_address is None and self.rssi is None and self.timestamp is None:
            raise JsonElementNotFoundException

        # TODO ここで時間の✅を行いたくない
        # timestampがあまりにも古い(１年以上)場合は、現在の時刻に設定
        if self.timestamp < datetime.now(tz=timezone.utc) - timedelta(days=365):
            self.timestamp = datetime.now(tz=timezone.utc)

    # デバイスIDとMACアドレスが同じ場合は同じデバイスとして扱う
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.device_id == other.device_id) and (self.mac_address == other.mac_address)
        else:
            raise ValueError("Invalid data type")

    def to_dict(self):
        return {
            "name": self.name,
            "device_id": self.device_id,
            "mac_address": self.mac_address,
            "rssi": self.rssi,
            "timestamp": self.timestamp,
            "manufacture_id": self.manufacture_id,
        }

    def update(self, other):
        if isinstance(other, self.__class__):
            self.rssi = other.rssi
            self.timestamp = other.timestamp
            self.name = other.name  # おそらく不変
            self.manufacture_id = other.manufacture_id  # おそらく不変
        else:
            raise ValueError("Invalid data type")


class DeviceLogger:
    def __init__(self):
        self.data = []

    # forで回せるようにする(初期化)
    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.data):
            result = self.data[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration

    def log(self, data: DeviceData):
        self.data.append(data)

    def to_dict(self):
        d_dict = [d.to_dict() for d in self.data]
        sorted_dict = sorted(d_dict, key=lambda x: x["timestamp"], reverse=True)
        return sorted_dict

    def cleanup_old_data(self):
        CLEANUP_TIME = timedelta(minutes=5)  # TODO: 30分のほうがいい？
        cutoff_time = datetime.now(tz=timezone.utc) - CLEANUP_TIME
        self.data = [d for d in self.data if d.timestamp > cutoff_time]

    def valid_devices_length(self) -> int:
        valid_devices = set([d.mac_address for d in self.data])
        return len(valid_devices)


class NotJsonException(Exception):
    def __str__(self):
        return "Request body must be JSON"


class JsonElementNotFoundException(Exception):
    def __str__(self):
        return "Invalid or missing data"
