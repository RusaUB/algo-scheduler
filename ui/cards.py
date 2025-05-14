import pygame

class Card:
    """
    A simple UI card component for Pygame with centered text.
    """
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        font: pygame.font.Font,
        bg_color: tuple = (100, 100, 250),
        text_color: tuple = (255, 255, 255),
        border_color: tuple = (0, 0, 0),
        border_width: int = 2,
    ):
        # Rectangle defining the card's position and size
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.border_width = border_width

    def draw(self, screen: pygame.Surface):
        # Draw background
        pygame.draw.rect(screen, self.bg_color, self.rect)
        # Draw border
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)
        # Render and center text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
