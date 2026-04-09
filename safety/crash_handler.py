import asyncio
import logging
import yaml
import time
from smbus2 import SMBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrashHandler")

class CrashHandler:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['hardware']['imu']
        
        self.bus = SMBus(self.config['i2c_bus'])
        self.address = self.config['i2c_address']
        self.threshold = self.config['crash_threshold_g']
        self.is_active = True
        
        # Initialize MPU-6050 (Wake up)
        try:
            self.bus.write_byte_data(self.address, 0x6B, 0)
            logger.info("MPU-6050 Initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to init IMU: {e}")

    def read_raw_data(self, addr: int) -> float:
        # Read two 8-bit registers and combine them
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        value = (high << 8) | low
        if value > 32768:
            value -= 65536
        return value

    async def monitor(self, sos_callback):
        """
        Polls IMU every 50ms. If G-force exceeds threshold, 
        triggers the SOS callback.
        """
        logger.info("Starting Crash Monitor...")
        try:
            while self.is_active:
                # MPU-6050 default scale is +/- 2g. 
                # For 2.5G detection, ensure sensitivity is set to 4g/8g/16g.
                # Here we assume standard reading conversion for simplicity
                ax = self.read_raw_data(0x3B) / 16384.0
                ay = self.read_raw_data(0x3D) / 16384.0
                az = self.read_raw_data(0x3F) / 16384.0

                total_g = (ax**2 + ay**2 + az**2)**0.5
                
                if total_g > self.threshold:
                    logger.warning(f"CRASH DETECTED: {total_g:.2f}G")
                    await sos_callback(total_g)
                    # Sleep longer after a trigger to prevent double-firing
                    await asyncio.sleep(5) 
                
                await asyncio.sleep(self.config['poll_rate'])
        except Exception as e:
            logger.error(f"IMU Monitor Error: {e}")
        finally:
            self.bus.close()

if __name__ == "__main__":
    # Standalone Test
    async def dummy_sos(g_force):
        print(f"!!! SOS TRIGGERED with {g_force}G !!!")

    handler = CrashHandler()
    try:
        asyncio.run(handler.monitor(dummy_sos))
    except KeyboardInterrupt:
        pass