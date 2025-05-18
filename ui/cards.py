import pygame

# Vertical offset (in pixels) to push all cards below top controls
CARD_Y_OFFSET = 80

class Card:
    """
    A simple UI card component for Pygame with a title and optional description,
    left-aligned, with rounded corners, and globally offset downwards.
    """
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        description: str,
        title_font: pygame.font.Font,
        desc_font: pygame.font.Font,
        bg_color: tuple = (100, 100, 250),
        title_color: tuple = (0, 0, 0),
        desc_color: tuple = (0, 0, 0),
        border_color: tuple = (0, 0, 0),
        border_width: int = 2,
        corner_radius: int = 8,
        padding_top: int = 10,
        padding_between: int = 5,
        padding_left: int = 10,
    ):
        # Base rectangle (before offset) defining the card's position and size
        self.base_rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.description = description
        self.title_font = title_font
        self.desc_font = desc_font
        self.bg_color = bg_color
        self.title_color = title_color
        self.desc_color = desc_color
        self.border_color = border_color
        self.border_width = border_width
        self.corner_radius = corner_radius
        self.padding_top = padding_top
        self.padding_between = padding_between
        self.padding_left = padding_left

    @property
    def rect(self) -> pygame.Rect:
        """
        The rendered rectangle of this card, moved down by the global offset.
        """
        return self.base_rect.move(0, CARD_Y_OFFSET)

    def draw(self, screen: pygame.Surface):
        rect = self.rect

        # background & border (unchanged)…
        pygame.draw.rect(screen, self.bg_color, rect, border_radius=self.corner_radius)
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, rect,
                             self.border_width, border_radius=self.corner_radius)

        # title (unchanged)…
        title_surf = self.title_font.render(self.title, True, self.title_color)
        title_rect = title_surf.get_rect(
            topleft=(rect.left + self.padding_left,
                     rect.top + self.padding_top)
        )
        screen.blit(title_surf, title_rect)

        # multiline description
        if self.description:
            y = title_rect.bottom + self.padding_between
            for line in self.description.splitlines():
                line_surf = self.desc_font.render(line, True, self.desc_color)
                screen.blit(line_surf, (rect.left + self.padding_left, y))
                y += line_surf.get_height() + self.padding_between
