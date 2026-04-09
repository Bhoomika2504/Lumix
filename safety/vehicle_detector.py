import asyncio
import logging
import yaml
import RPi.GPIO as GPIO
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VehicleDetector")

class VehicleDetector:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            full_config = yaml.safe_load(f)
            self.config = full_config['hardware']['sonar']
        
        self.threshold = self.config['threshold_cm']
        self.poll_rate = self.config['poll_rate']
        
        # Tracking consecutive triggers for debouncing {direction: count}
        self.trigger_counts = {"LEFT": 0, "RIGHT": 0, "REAR": 0}
        self.last_alert_time = {"LEFT": 0, "RIGHT": 0, "REAR": 0}
        
        self.setup_gpio()

    def setup_gpio(self):
        """Initializes GPIO pins for all three sensors."""
        GPIO.setmode(GPIO.BCM)
        for direction in ['left', 'right', 'rear']:
            pins = self.config[direction]
            GPIO.setup(pins['trig'], GPIO.OUT)
            GPIO.setup(pins['echo'], GPIO.IN)
            GPIO.output(pins['trig'], False)
        logger.info("Sonar GPIO pins configured.")

    def get_distance(self, direction: str) -> float:
        """Standard HC-SR04 distance measurement logic."""
        pins = self.config[direction.lower()]
        trig = pins['trig']
        echo = pins['echo']

        # Send 10us pulse
        GPIO.output(trig, True)
        time.sleep(0.00001)
        GPIO.output(trig, False)

        pulse_start = time.time()
        pulse_end = time.time()

        # Timeout logic to prevent hanging if sensor fails
        timeout = time.time() + 0.1
        while GPIO.input(echo) == 0:
            pulse_start = time.time()
            if pulse_start > timeout: return 999.0

        while GPIO.input(echo) == 1:
            pulse_end = time.time()
            if pulse_end > timeout: return 999.0

        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2 # Speed of sound (cm/s)
        return round(distance, 2)

    async def monitor(self, alert_callback):
        """
        Polls all sensors. Triggers alert_callback if 3 consecutive 
        readings are below threshold.
        """
        logger.info("Starting Vehicle Detection Monitor...")
        try:
            while True:
                for direction in ["LEFT", "RIGHT", "REAR"]:
                    dist = self.get_distance(direction)
                    
                    if dist < self.threshold:
                        self.trigger_counts[direction] += 1
                    else:
                        self.trigger_counts[direction] = 0 # Reset if object leaves

                    # Rule: 3 consecutive readings AND 3 seconds since last alert
                    current_time = time.time()
                    if (self.trigger_counts[direction] >= 3 and 
                        current_time - self.last_alert_time[direction] > 3):
                        
                        logger.warning(f"⚠ VEHICLE DETECTED AT {direction}: {dist}cm")
                        self.last_alert_time[direction] = current_time
                        
                        # Trigger both HUD popup and Voice alert via callback
                        await alert_callback(direction)

                await asyncio.sleep(self.poll_rate)
        except Exception as e:
            logger.error(f"Sonar Monitor Error: {e}")
        finally:
            GPIO.cleanup()

if __name__ == "__main__":
    # Standalone hardware test
    async def dummy_alert(direction):
        print(f"UI ALERT: Vehicle approaching from {direction}!")

    detector = VehicleDetector()
    try:
        asyncio.run(detector.monitor(dummy_alert))
    except KeyboardInterrupt:
        print("Cleaning up...")