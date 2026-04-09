import openrouteservice
import yaml
import logging
from typing import List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NavigationRouter")

class NavigationRouter:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.api_key = self.config['api_keys']['openrouteservice']
        self.client = openrouteservice.Client(key=self.api_key)
        
        # Mapping ORS 'type' numbers to HUD arrow names
        # 0: Left, 1: Right, 2: Sharp Left, 3: Sharp Right, etc.
        self.maneuver_map = {
            0: "LEFT", 1: "RIGHT", 2: "SHARP_LEFT", 3: "SHARP_RIGHT",
            4: "SLIGHT_LEFT", 5: "SLIGHT_RIGHT", 6: "STRAIGHT",
            12: "KEEP_LEFT", 13: "KEEP_RIGHT"
        }

    def get_route(self, start_coords: Tuple[float, float], destination: str):
        """
        Geocodes the destination and fetches turn-by-turn directions.
        ORS uses [Longitude, Latitude] format.
        """
        try:
            # 1. Geocode Destination (Name -> Coords)
            geocode = self.client.pelias_search(text=destination, size=1)
            if not geocode['features']:
                return None
            
            dest_coords = geocode['features'][0]['geometry']['coordinates']
            logger.info(f"Navigating to: {destination} at {dest_coords}")

            # 2. Get Directions
            # profile 'cycling-regular' or 'driving-car'
            routes = self.client.directions(
                coordinates=[start_coords, dest_coords],
                profile='driving-car',
                format='json'
            )

            # 3. Extract Steps
            steps = routes['routes'][0]['segments'][0]['steps']
            return self._process_steps(steps)

        except Exception as e:
            logger.error(f"Navigation Error: {e}")
            return None

    def _process_steps(self, steps: List[dict]):
        """Simplifies raw API data into HUD-friendly instructions."""
        formatted_steps = []
        for s in steps:
            instruction = {
                "distance": s['distance'], # in meters
                "instruction": s['instruction'],
                "arrow": self.maneuver_map.get(s['type'], "STRAIGHT")
            }
            formatted_steps.append(instruction)
        return formatted_steps

if __name__ == "__main__":
    # Test: From TCOER to Pune Station
    nav = NavigationRouter()
    # Replace with your actual lon/lat from GPS
    test_start = (73.8677, 18.4575) 
    path = nav.get_route(test_start, "Pune Railway Station")
    
    if path:
        for step in path:
            print(f"In {step['distance']}m: {step['arrow']} -> {step['instruction']}")