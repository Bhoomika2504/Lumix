import edge_tts
import asyncio
import pygame
import os
import uuid

class HelmetSpeaker:
    def __init__(self, voice: str = "en-US-JennyNeural"):  # Changed to a clear, female voice
        self.voice = voice
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    async def speak(self, text: str):
        # 1. Generate a unique, temporary filename
        temp_file = f"voice_output_{uuid.uuid4().hex[:6]}.mp3"
        
        try:
            # 2. Save the AI's voice to this unique file
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_file)
            
            # 3. Load and play the audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # 4. Wait for it to finish speaking
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
            # 5. Tell PyGame to let go of the file
            pygame.mixer.music.unload()
            
        except Exception as e:
            print(f"Speaker Error: {e}")
            
        finally:
            # 6. Delete the file so your computer doesn't fill up with MP3s!
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as cleanup_error:
                print(f"Cleanup Error (Ignored): {cleanup_error}")