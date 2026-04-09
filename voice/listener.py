import os
import pvporcupine
import pyaudio
import struct
import whisper
import asyncio
import logging
import wave
import yaml
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HelmetListener")

class HelmetListener:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 1. Initialize Porcupine Wake Word ("Hey Helmet" / "Jarvis" / "Custom")
        # Note: You need a Picovoice Access Key from their console
        self.porcupine = pvporcupine.create(
            access_key=self.config['api_keys']['pvporcupine'],
            keywords=['hey Lumix'] 
        )
        
        # 2. Load Whisper Model (Using 'tiny' for Raspberry Pi speed)
        logger.info("Loading Whisper 'tiny' model (this may take a moment)...")
        self.stt_model = whisper.load_model("tiny")
        
        # 3. Audio Stream Setup
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )
        
        self.is_listening = True

    def _record_command(self, duration=4) -> str:
        """Records audio for 4 seconds after wake word is detected."""
        logger.info("Listening for command...")
        frames = []
        # Calculate frames needed for duration
        for _ in range(0, int(self.porcupine.sample_rate / self.porcupine.frame_length * duration)):
            data = self.audio_stream.read(self.porcupine.frame_length)
            frames.append(data)
            
        # Save to temporary file for Whisper
        temp_file = "command.wav"
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.porcupine.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        return temp_file

    async def listen_loop(self, command_callback):
        """Continuous loop checking for wake word."""
        logger.info("Wake word engine active. Say 'Hey Helmet'...")
        try:
            while self.is_listening:
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm_unpacked = struct.unpack_樂('h' * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm_unpacked)
                
                if keyword_index >= 0:
                    logger.info("Wake word DETECTED!")
                    
                    # 1. Notify user (Maybe a beep or HUD change)
                    # 2. Record the speech
                    audio_path = self._record_command()
                    
                    # 3. Transcribe (Offload to thread so it doesn't block)
                    result = await asyncio.to_thread(self.stt_model.transcribe, audio_path)
                    text = result['text'].strip()
                    
                    if text:
                        logger.info(f"Transcribed: {text}")
                        await command_callback(text)
                
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Listener Error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        self.audio_stream.close()
        self.pa.terminate()
        self.porcupine.delete()

if __name__ == "__main__":
    # Standalone Test
    async def handle_cmd(text):
        print(f"Executing: {text}")

    listener = HelmetListener()
    try:
        asyncio.run(listener.listen_loop(handle_cmd))
    except KeyboardInterrupt:
        pass