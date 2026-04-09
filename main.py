import asyncio
import logging
import platform
import pygame
import datetime
import speech_recognition as sr
import json
import cv2
import numpy as np
from ultralytics import YOLO
from geopy.geocoders import Nominatim

from ui.hud import SmartHUD
from voice.assistant import HelmetAssistant
from voice.speaker import HelmetSpeaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LUMIX_DEMO")

class SmartHUDController:
    def __init__(self):
        self.hud = SmartHUD()
        self.ai = HelmetAssistant()
        self.speaker = HelmetSpeaker()
        self.is_running = True
        self.recognizer = sr.Recognizer()
        self.geolocator = Nominatim(user_agent="tcoer_lumix_project_bhoomika_v1")
        
        self.sos_active = False
        self.auto_alert_active = False 
        
        self.live_lat = 18.4575
        self.live_lon = 73.8677
        self.current_speed = 0.0 # Starts at 0
        self.locked_crash_data = {}
        
        logger.info("Loading YOLOv8 AI Model...")
        self.yolo = YOLO("yolov8n.pt") 
        self.cap = cv2.VideoCapture(0) 
        self.vehicle_history = {} 

    async def vision_system_loop(self):
        while self.is_running:
            success, frame = self.cap.read()
            if not success:
                await asyncio.sleep(0.1)
                continue

            frame = cv2.resize(frame, (1024, 600))
            results = self.yolo.track(frame, persist=True, classes=[2, 3, 5, 7], verbose=False)
            collision_danger = False

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xywh.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().tolist()

                for box, track_id in zip(boxes, track_ids):
                    x, y, w, h = box
                    area = w * h
                    top_left = (int(x - w/2), int(y - h/2))
                    bottom_right = (int(x + w/2), int(y + h/2))
                    cv2.rectangle(frame, top_left, bottom_right, (0, 255, 200), 2)

                    if track_id in self.vehicle_history:
                        old_area = self.vehicle_history[track_id]
                        growth_rate = area / old_area

                        if growth_rate > 1.15 and area > 15000: 
                            collision_danger = True
                            cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 4) 
                            cv2.putText(frame, "IMMINENT CRASH!", (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

                    self.vehicle_history[track_id] = area

            current_ids = set(track_ids) if results[0].boxes.id is not None else set()
            self.vehicle_history = {k: v for k, v in self.vehicle_history.items() if k in current_ids}

            if collision_danger and not self.auto_alert_active and not self.sos_active:
                asyncio.create_task(self.trigger_auto_alert("🛑 BRAKE NOW: COLLISION IMMINENT", "Danger ahead. Brake immediately."))

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pg_img = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
            self.hud.bg_frame = pg_img

            await asyncio.sleep(0.03) 

    async def trigger_auto_alert(self, visual_text, audio_text):
        self.auto_alert_active = True
        self.hud.update_data("alert", visual_text)
        await self.speaker.speak(audio_text)
        await asyncio.sleep(4)
        if self.hud.data.get("alert") == visual_text:
            self.hud.update_data("alert", None)
        self.auto_alert_active = False

    async def simulate_live_metrics(self):
        """Simulates GPS movement and natural deceleration."""
        while self.is_running:
            if not self.sos_active:
                self.live_lat += 0.00005
                self.live_lon += 0.00005
                
                # Check if the throttle 'S' is NOT being held
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_s]:
                    # NATURAL DECELERATION: Friction slows the bike down over time
                    if self.current_speed > 0:
                        self.current_speed -= 3.0 
                        self.current_speed = max(0.0, self.current_speed)
                        self.hud.update_data("speed", self.current_speed)
                
                # OVERSPEEDING AI CHECK (> 80 KM/H)
                if self.current_speed > 80.0 and not self.auto_alert_active and not self.sos_active:
                    asyncio.create_task(self.trigger_auto_alert("⚠ OVER SPEEDING DETECTED", "Please slow down. You have exceeded the safety limit."))

            await asyncio.sleep(1)

    def _get_readable_address(self, lat, lon):
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10)
            if location: return location.address
            return "Address unavailable"
        except Exception:
            return "GPS Signal Lost"

    async def handle_voice_command(self, text: str):
        logger.info(f"🎤 You said: {text}")
        self.hud.update_data("alert", "LUMIX IS THINKING...")
        response = await self.ai.ask(text)
        self.hud.update_data("alert", response)
        asyncio.create_task(self.speaker.speak(response))
        await asyncio.sleep(6)
        if self.hud.data.get("alert") == response:
            self.hud.update_data("alert", None)

    def _record_audio_sync(self):
        with sr.Microphone() as source:
            logger.info("Speak now!")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                return self.recognizer.recognize_google(audio)
            except Exception:
                return None

    async def trigger_live_listening(self):
        self.hud.update_data("alert", "🎤 LISTENING...")
        spoken_text = await asyncio.to_thread(self._record_audio_sync)
        if spoken_text:
            text_lower = spoken_text.lower()
            if self.sos_active and ("cancel" in text_lower or "abort" in text_lower):
                await self.cancel_sos()
            else:
                await self.handle_voice_command(spoken_text)
        else:
            if not self.sos_active: 
                self.hud.update_data("alert", "Try again.")
                await asyncio.sleep(2)
                self.hud.update_data("alert", None)

    async def start_sos_protocol(self, impact="8.5G"):
        if self.sos_active: return 
        self.sos_active = True
        logger.warning(f"DEMO: Crash Triggered!")
        
        self.locked_crash_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lat": self.live_lat,
            "lon": self.live_lon,
            "impact": impact
        }
        
        self.hud.update_data("alert", "!!! CRASH DETECTED !!!")
        
        await self.speaker.speak("Impact detected. SOS protocol initiating.")
        await asyncio.sleep(0.5)
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        
        for i in range(5, 0, -1):
            if not self.sos_active: break 
            self.hud.update_data("alert", f"SOS INITIATING IN: {i}s")
            await asyncio.sleep(1)
            
        if self.sos_active:
            self.sos_active = False
            await self.dispatch_emergency_services()

    async def cancel_sos(self):
        if self.sos_active:
            self.sos_active = False
            self.hud.update_data("alert", "SOS CANCELED")
            await self.speaker.speak("SOS protocol aborted. Glad you are safe.")
            await asyncio.sleep(3)
            self.hud.update_data("alert", None)

    async def dispatch_emergency_services(self):
        self.hud.update_data("alert", "SOS DISPATCHED")
        await self.speaker.speak("SOS message dispatched.")
        
        readable_address = await asyncio.to_thread(self._get_readable_address, self.locked_crash_data["lat"], self.locked_crash_data["lon"])
        
        crash_data = {
            "status": "CRITICAL",
            "timestamp": self.locked_crash_data["timestamp"],
            "lat": self.locked_crash_data["lat"],
            "lon": self.locked_crash_data["lon"],
            "location": f"Lat: {self.locked_crash_data['lat']:.5f}, Lon: {self.locked_crash_data['lon']:.5f}",
            "address": readable_address,
            "impact": self.locked_crash_data["impact"]
        }
        
        with open("alert_data.json", "w", encoding="utf-8") as f:
            json.dump(crash_data, f, ensure_ascii=False)
            
        await asyncio.sleep(5)
        self.hud.update_data("alert", None)

    async def presentation_simulator(self):
        logger.info("=== LUMIX DEMO MODE ACTIVE ===")
        while self.is_running:
            # MAIN.PY NOW HAS EXCLUSIVE CONTROL OF THE KEYBOARD
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.is_running = False
                    self.hud.running = False # Safely shuts down the HUD
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: 
                        self.is_running = False
                        self.hud.running = False
                        
                    # Live Mic
                    elif event.key == pygame.K_SPACE: asyncio.create_task(self.trigger_live_listening())
                    
                    # Crash & Cancel Triggers
                    elif event.key == pygame.K_c: asyncio.create_task(self.start_sos_protocol("8.5G"))
                    elif event.key == pygame.K_q: asyncio.create_task(self.cancel_sos())
                    
                    # Demo Hardware Sensors
                    elif event.key == pygame.K_v: asyncio.create_task(self.trigger_demo_event("VEHICLE"))
                    elif event.key == pygame.K_p: asyncio.create_task(self.trigger_auto_alert("🛑 BRAKE NOW: COLLISION IMMINENT", "Danger ahead. Brake immediately."))
            
            # --- CONTINUOUS THROTTLE CHECK ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_s]:
                self.current_speed += 1.0  
                self.current_speed = min(self.current_speed, 140.0) 
                self.hud.update_data("speed", self.current_speed)
                
            await asyncio.sleep(0.05)

    async def run_system(self):
        tasks = [
            self.hud.render_loop(), 
            self.presentation_simulator(), 
            self.simulate_live_metrics(),
            self.vision_system_loop() 
        ]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Main Loop Error: {e}")
        finally:
            self.is_running = False
            self.cap.release()
            pygame.quit()

if __name__ == "__main__":
    controller = SmartHUDController()
    try:
        asyncio.run(controller.run_system())
    except KeyboardInterrupt: pass