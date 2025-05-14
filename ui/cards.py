import pygame

class Card:
    """
    A simple UI card component for Pygame with a title and optional description, left-aligned, with rounded corners.
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
        # Rectangle defining the card's position and size
        self.rect = pygame.Rect(x, y, width, height)
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

    def draw(self, screen: pygame.Surface):
        # Draw background with rounded corners
        pygame.draw.rect(
            screen,
            self.bg_color,
            self.rect,
            border_radius=self.corner_radius
        )
        # Draw border with rounded corners
        if self.border_width > 0:
            pygame.draw.rect(
                screen,
                self.border_color,
                self.rect,
                self.border_width,
                border_radius=self.corner_radius
            )

        # Render and position title (left-aligned)
        title_surf = self.title_font.render(self.title, True, self.title_color)
        title_rect = title_surf.get_rect(
            topleft=(self.rect.left + self.padding_left, self.rect.top + self.padding_top)
        )
        screen.blit(title_surf, title_rect)

        # Render and position description below title (left-aligned)
        if self.description:
            desc_surf = self.desc_font.render(self.description, True, self.desc_color)
            desc_rect = desc_surf.get_rect(
                topleft=(self.rect.left + self.padding_left, title_rect.bottom + self.padding_between)
            )
            screen.blit(desc_surf, desc_rect)
