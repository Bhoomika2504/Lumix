import pygame
import asyncio

class SmartHUD:
    def __init__(self):
        pygame.init()
        self.width = 1024
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("LUMIX OS - AR Vision UI")

        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("Consolas", 24)
        self.font_md = pygame.font.SysFont("Consolas", 40, bold=True)
        self.font_lg = pygame.font.SysFont("Consolas", 90, bold=True)
        
        self.colors = {
            "bg": (10, 15, 20),
            "accent": (0, 255, 200),
            "warning": (255, 80, 80),
            "text": (240, 240, 240),
            "panel": (25, 35, 45)
        }
        
        self.data = {
            "speed": 0,
            "battery": 85,
            "alert": None, 
            "status": "SYSTEM NOMINAL"
        }
        
        # NEW: Holds the live camera feed
        self.bg_frame = None 
        self.running = True

    def draw_rounded_rect(self, surface, color, rect, radius=15, alpha=255):
        temp_surface = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(temp_surface, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surface.blit(temp_surface, (rect[0], rect[1]))

    async def render_loop(self):
        while self.running:
            # ---> WE DELETED THE EVENT.GET() LOOP FROM HERE <---

            # Draw Camera Feed (or dark background if camera is off)
            if self.bg_frame:
                self.screen.blit(self.bg_frame, (0, 0))
            else:
                self.screen.fill(self.colors["bg"])

            # Left Panel (Speed & Data)
            self.draw_rounded_rect(self.screen, self.colors["panel"], (30, 30, 250, 200), alpha=180)
            speed_text = self.font_lg.render(f"{int(self.data['speed'])}", True, self.colors["accent"])
            self.screen.blit(speed_text, (50, 50))
            unit_text = self.font_sm.render("KM/H", True, self.colors["text"])
            self.screen.blit(unit_text, (60, 140))

            # Top Right (Battery & Status)
            self.draw_rounded_rect(self.screen, self.colors["panel"], (self.width - 330, 30, 300, 60), alpha=180)
            bat_text = self.font_sm.render(f"BAT:{self.data['battery']}% | GPS: OK", True, self.colors["text"])
            self.screen.blit(bat_text, (self.width - 310, 45))

            # Dynamic Center Alert Overlay
            if self.data['alert']:
                color = self.colors["warning"] if "SOS" in self.data['alert'] or "CRASH" in self.data['alert'] or "BRAKE" in self.data['alert'] else self.colors["accent"]
                self.draw_rounded_rect(self.screen, color, (50, self.height - 200, self.width - 100, 150), alpha=230)
                alert_msg = self.font_md.render(self.data['alert'], True, (10, 10, 10))
                text_rect = alert_msg.get_rect(center=(self.width/2, self.height - 125))
                self.screen.blit(alert_msg, text_rect)

            pygame.display.flip()
            await asyncio.sleep(1/30)

    def update_data(self, key, value):
        self.data[key] = value

if __name__ == "__main__":
    hud = SmartHUD()
    asyncio.run(hud.render_loop())