class Container:
    def __init__(self, font, direction="col", spacing=10, text_color=(0,0,0)):
        self.font        = font
        self.direction   = direction
        self.spacing     = spacing
        self.text_color  = text_color
        self.items       = []

    def add_text(self, text):
        surf = self.font.load().render(text, True, self.text_color)
        self.items.append(surf)

    def draw(self, screen, x, y):
        cur_x, cur_y = x, y
        for surf in self.items:
            screen.blit(surf, (cur_x, cur_y))
            w, h = surf.get_size()
            if self.direction == "col":
                cur_y += h + self.spacing
            else:
                cur_x += w + self.spacing

    def get_height(self):
        if not self.items:
            return 0
        heights = [s.get_height() for s in self.items]
        return sum(heights) + self.spacing * (len(heights)-1)

    def get_width(self):
        if not self.items:
            return 0
        widths = [s.get_width() for s in self.items]
        if self.direction == "col":
            return max(widths)
        else:
            return sum(widths) + self.spacing * (len(widths)-1)
