import pygame
import yaml
import os

class NavigationUI:
    def __init__(self, screen, config_path: str = "config.yaml"):
        self.screen = screen
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['ui']
            
        self.font = pygame.font.SysFont("Share Tech Mono", 50)
        self.color = self.config['colors']['nav'] # Green (#00FF88)
        
        # Dictionary to store loaded arrow images
        self.arrows = {}
        self.load_assets()

    def load_assets(self):
        """
        Loads arrow icons. 
        Tip: Use simple PNGs with transparency for the best HUD look.
        """
        arrow_types = ["LEFT", "RIGHT", "STRAIGHT", "SHARP_LEFT", "SHARP_RIGHT"]
        asset_path = "assets/nav/" # Create this folder and add icons
        
        for a_type in arrow_types:
            img_path = f"{asset_path}{a_type.lower()}.png"
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                # Scale to fit center zone (e.g., 200x200)
                self.arrows[a_type] = pygame.transform.scale(img, (200, 200))
            else:
                # Fallback if image is missing (Draws a simple triangle/text)
                self.arrows[a_type] = None

    def draw(self, direction: str, distance: float):
        """
        Renders the current navigation step in the CENTER of the HUD.
        """
        if not direction:
            return

        # 1. Draw the Arrow Icon
        center_x = self.config['width'] // 2
        center_y = self.config['height'] // 2
        
        icon = self.arrows.get(direction)
        if icon:
            rect = icon.get_rect(center=(center_x, center_y - 50))
            self.screen.blit(icon, rect)
        else:
            # Text Fallback if icons aren't ready
            text_dir = self.font.render(direction, True, self.color)
            self.screen.blit(text_dir, (center_x - 50, center_y - 100))

        # 2. Draw Distance Text (e.g., "250 m")
        dist_text = self.font.render(f"{int(distance)} m", True, (255, 255, 255))
        dist_rect = dist_text.get_rect(center=(center_x, center_y + 100))
        self.screen.blit(dist_text, dist_rect)

if __name__ == "__main__":
    # Test script for UI alignment
    pygame.init()
    cfg = {"width": 1280, "height": 720, "colors": {"nav": (0, 255, 136)}}
    screen = pygame.display.set_mode((1280, 720))
    nav_ui = NavigationUI(screen)
    
    running = True
    while running:
        screen.fill((0, 0, 0))
        nav_ui.draw("LEFT", 150.5)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
    pygame.quit()