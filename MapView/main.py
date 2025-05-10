import asyncio
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import Datasource
import os
from kivy.clock import Clock
from Datavisualizer import DataVisualizer


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = 1 
        self.datasource = Datasource(self.user_id)
        self.car_marker = None
        self.map_layer = None
        self.update_event = None
        self.current_position = (50.4501, 30.5234)  # Київ

    def on_start(self):

        self.map_layer = LineMapLayer()
        self.mapview.add_layer(self.map_layer, mode="scatter")
        
        self.car_marker = MapMarker(lat=self.current_position[0], lon=self.current_position[1], 
                                    source='images/car.png')
        self.mapview.add_marker(self.car_marker)
        
        self.map_layer.add_point([self.current_position[0], self.current_position[1]])
        
        self.update_event = Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        new_points = self.datasource.get_new_points()
        
        for point in new_points:
            latitude, longitude, road_state = point
            
            self.update_car_marker((latitude, longitude))
            
            self.map_layer.add_point([latitude, longitude])
            
            if road_state == "average":
                self.set_pothole_marker((latitude, longitude))
            elif road_state == "poor":
                self.set_bump_marker((latitude, longitude))

    def update_car_marker(self, point):
        if self.car_marker:
            self.mapview.remove_marker(self.car_marker)
            
        self.car_marker = MapMarker(lat=point[0], lon=point[1], source='images/car.png')
        self.mapview.add_marker(self.car_marker)
        self.current_position = point
        
        self.mapview.center_on(point[0], point[1])

    def set_pothole_marker(self, point):
        pothole_marker = MapMarker(lat=point[0], lon=point[1], source='images/pothole.png')
        self.mapview.add_marker(pothole_marker)

    def set_bump_marker(self, point):
        bump_marker = MapMarker(lat=point[0], lon=point[1], source='images/bump.png')
        self.mapview.add_marker(bump_marker)

    def build(self):
        self.mapview = MapView(zoom=11, lat=50.450001, lon=30.523333)
        
        self.visualizer = DataVisualizer(self.mapview)
        
        self.visualizer.load_data_from_csv('/Users/romsyaborysenko/Documents/KPI/Семестр 2/IoT Development/IoT_Project/MapView/data.csv')
        
        self.visualizer.visualize_on_map()
        
        self.mapview.bind(zoom=self.visualizer.update_lines_on_zoom)
        
        return self.mapview


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MapViewApp().async_run(async_lib="asyncio"))
    loop.close()