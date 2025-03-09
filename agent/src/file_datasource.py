import csv
from datetime import datetime
from domain.aggregated_data import AggregatedData
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking

class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str, parking_filename) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename
        self.accelerometer_data = []
        self.gps_data = []
        self.parking_data = []
        self.index = 0
        self.reading = False

    def startReading(self):
        self.reading = True
        self.accelerometer_data = self._read_csv(self.accelerometer_filename)
        self.gps_data = self._read_csv(self.gps_filename)
        self.parking_data = self._read_csv(self.parking_filename)
        self.index = 0

    def read(self) -> AggregatedData:
        if not self.reading:
            raise RuntimeError("Читання не було розпочате. Викличте startReading().")

        if self.index >= len(self.accelerometer_data) or self.index >= len(self.gps_data) or self.index >= len(self.parking_data):
            self.index = 0 

        acc_x, acc_y, acc_z = map(int, self.accelerometer_data[self.index])
        lon, lat = map(float, self.gps_data[self.index])
        parking_empty_count, parking_lon, parking_lat = map(float, self.parking_data[self.index])

        self.index += 1

        return AggregatedData(
            accelerometer=Accelerometer(acc_x, acc_y, acc_z),
            gps=Gps(lon, lat),
            parking=Parking(
                empty_count=parking_empty_count,
                gps=Gps(parking_lon, parking_lat)
            ),
            timestamp=datetime.now(),
            user_id=self.index
        )

    def stopReading(self):
        self.reading = False

    def _read_csv(self, filename):
        with open(filename, "r") as file:
            reader = csv.reader(file)
            next(reader)  # Пропустити заголовки
            return [row for row in reader]