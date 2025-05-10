import pandas as pd
import numpy as np
import kivy_garden.mapview
from kivy_garden.mapview import MapView, MapMarker
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
import math
from lineMapLayer import LineMapLayer
from kivy.graphics.instructions import InstructionGroup

class MapLine(InstructionGroup):
    def __init__(self, mapview, lat1, lon1, lat2, lon2, color=(1, 0, 0, 1), width=2):
        super(MapLine, self).__init__()
        self.mapview = mapview
        self.lat1 = lat1
        self.lon1 = lon1
        self.lat2 = lat2
        self.lon2 = lon2
        self.color = color
        self.width = width
        
        self.color_instr = Color(*color)
        self.add(self.color_instr)
        
        self.line = Line(width=width)
        self.add(self.line)
        
        self.update_position()
        
    def update_position(self):
        x1, y1 = self._get_screen_pos(self.lat1, self.lon1)
        x2, y2 = self._get_screen_pos(self.lat2, self.lon2)
        
        self.line.points = [x1, y1, x2, y2]
    
    def _get_screen_pos(self, lat, lon):
        center_x, center_y = self.mapview.center_x, self.mapview.center_y
        
        zoom = self.mapview.zoom
        
        scale = 2 ** zoom * 256
        x = center_x + (lon - self.mapview.lon) * scale / 360
        y = center_y + 0.5 * math.log((1 + math.sin(lat * math.pi / 180)) / (1 - math.sin(lat * math.pi / 180))) * scale / (2 * math.pi)
        
        return x, y

class DataVisualizer:
    def __init__(self, mapview):
        self.mapview = mapview
        self.markers = []
        self.lines = []
        self.data = None
        self.road_state_colors = {
            "good": get_color_from_hex("#00FF00"),
            "medium": get_color_from_hex("#FFFF00"),
            "bad": get_color_from_hex("#FF0000")
        }
        
    def load_data_from_csv(self, csv_path):
        df = pd.read_csv(csv_path, names=['X', 'Y', 'Z'], skiprows=lambda x: x % 2 == 1)
        
        df = df.dropna(how='all')
        
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df['Z'] = pd.to_numeric(df['Z'], errors='coerce')
        
        df = df.dropna()

        df['road_state'] = df.apply(self._calculate_road_state, axis=1)
        
        start_lat, start_lon = 50.450001, 30.523333
        
        coordinates = []
        current_lat, current_lon = start_lat, start_lon
        
        for _, row in df.iterrows():
            lat_change = row['X'] / 100000.0
            lon_change = row['Y'] / 100000.0
            
            current_lat += lat_change
            current_lon += lon_change
            
            coordinates.append({
                'latitude': current_lat,
                'longitude': current_lon,
                'road_state': row['road_state']
            })
        
        self.data = coordinates
        return coordinates
    
    def _calculate_road_state(self, row):
        x, y, z = row['X'], row['Y'], row['Z']
       
        magnitude = math.sqrt(x**2 + y**2)
        
        if magnitude < 500:
            return "good"
        elif magnitude < 5000:
            return "medium"
        else:
            return "bad"
    
    def visualize_on_map(self):
        if not self.data:
            return
        
        self._clear_visualization()
        
        points = []
        prev_point = None
        
        for point in self.data:
            marker = kivy_garden.mapview.MapMarker(lat=point['latitude'], lon=point['longitude'])
            self.mapview.add_marker(marker)
            self.markers.append(marker)
            
            points.append((point['latitude'], point['longitude'], point['road_state']))
            
            if prev_point:
                self._add_line(prev_point, (point['latitude'], point['longitude'], point['road_state']))
            
            prev_point = (point['latitude'], point['longitude'], point['road_state'])
        
        if points:
            self.mapview.center_on(points[0][0], points[0][1])
            self.mapview.zoom = 15
    
    def _add_line(self, point1, point2):
        road_state = point2[2]
        color = self.road_state_colors.get(road_state, get_color_from_hex("#FFFFFF"))
        
        line = MapLine(
            self.mapview, 
            point1[0], point1[1], 
            point2[0], point2[1], 
            color=color, 
            width=dp(3)
        )
        
        self.mapview.canvas.add(line)
        self.lines.append(line)
    
    def _clear_visualization(self):
        for marker in self.markers:
            self.mapview.remove_marker(marker)
        self.markers = []
        
        for line in self.lines:
            self.mapview.canvas.remove(line)
        self.lines = []
    
    def update_lines_on_zoom(self, *args):
        for line in self.lines:
            line.update_position()