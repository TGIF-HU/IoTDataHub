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
            time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

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
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "mac_address": self.mac_address,
            "manufacture_id": self.manufacture_id,
            "last_seen": self.timestamp,
            "rssi_data": {
                self.device_id: {
                    "rssi": self.rssi,
                    "timestamp": self.timestamp
                }
            }
        }

    def update(self, other):
        self.rssi = other.rssi
        self.timestamp = other.timestamp
        # self.name = other.name # おそらく不変
        # self.manufacture_id = other.manufacture_id


class DeviceLogger:
    def __init__(self):
        self.index = 0
        self.data = []

    # forで回せるようにする
    def __iter__(self):
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
        return [d.to_dict() for d in self.data]


class NotJsonException(Exception):
    def __str__(self):
        return "Request body must be JSON"


class JsonElementNotFoundException(Exception):
    def __str__(self):
        return "Invalid or missing data"
