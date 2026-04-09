import os
import logging
import aiohttp
import asyncio
import platform
from dotenv import load_dotenv

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HelmetAI")

class HelmetAssistant:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in .env file!")
            
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={self.api_key}"
        
        # RELAXED PROMPT: Forces Lumix to actually answer your questions!
        self.system_prompt = (
            "You are Lumix, a highly intelligent and friendly motorcycle helmet AI assistant. "
            "You must directly answer whatever the rider asks you, whether it is about weather, trivia, directions, or casual conversation. "
            "Do NOT refuse to answer questions. Do NOT constantly tell the rider to watch the road. "
            "Keep your answers concise, strictly 1 to 2 sentences maximum. Do not use markdown, bolding, or lists."
        )

    async def ask(self, query: str) -> str:
        if not self.api_key:
            return "API Key missing."

        payload = {
            "system_instruction": {
                "parts": [{"text": self.system_prompt}]
            },
            "contents": [
                {"parts": [{"text": query}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.7
            }
        }

        try:
            logger.info(f"Rider asked: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data['candidates'][0]['content']['parts'][0]['text']
                        return text.strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"Google API Rejected Request (Code {response.status}): {error_text}")
                        return "I am having a connection hiccup."
                        
        except Exception as e:
            logger.error(f"Connection Error: {e}")
            return "Connection trouble."

if __name__ == "__main__":
    async def test():
        assistant = HelmetAssistant()
        answer = await assistant.ask("What is the best Pokémon?")
        print(f"\nLumix says: {answer}\n")
        await asyncio.sleep(0.5)

    asyncio.run(test())