import RPi.GPIO as GPIO
import asyncio

class HelmetButton:
    def __init__(self, pin=26):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    async def monitor(self, short_press_cb, long_press_cb):
        """Detects clicks vs long presses (for SOS cancel)."""
        while True:
            if GPIO.input(self.pin) == GPIO.LOW:
                start_time = asyncio.get_event_loop().time()
                while GPIO.input(self.pin) == GPIO.LOW:
                    await asyncio.sleep(0.1)
                
                duration = asyncio.get_event_loop().time() - start_time
                if duration > 2.0:
                    await long_press_cb() # Long press for SOS
                else:
                    await short_press_cb() # Short press to wake Lumix
            await asyncio.sleep(0.1)