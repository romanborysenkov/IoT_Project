from domain.gps import Gps
from dataclasses import dataclass


@dataclass
class Parking:
    empty_count: float
    gps: Gps
    