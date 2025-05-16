import pygame

class Table:
    def __init__(self, screen_width, screen_height, font):
        self.screen_width   = screen_width
        self.screen_height  = screen_height
        self.font           = font
        self._last_rows     = 0
        self._last_spacing  = 0
        self._last_margin_x = 0

    def draw(self, screen, x, y, cols, processes, spacing=30):
        """
        x, y      – top-left of the table
        cols      – list of column headers
        processes – list of Process objects
        spacing   – row height
        """
        self._last_rows     = len(processes)
        self._last_spacing  = spacing
        self._last_margin_x = x

        table_w = self.screen_width - 2*x
        n_cols  = len(cols)
        col_w   = table_w / n_cols

        # Header
        hdr_rect = pygame.Rect(x, y, table_w, spacing)
        pygame.draw.rect(screen, (200,200,200), hdr_rect)
        for i,h in enumerate(cols):
            cx = x + col_w*i + col_w/2
            cy = y + spacing/2
            txt = self.font.load().render(h, True, (0,0,0))
            screen.blit(txt, txt.get_rect(center=(cx,cy)))
            pygame.draw.line(screen, (0,0,0),
                             (x + col_w*(i+1), y),
                             (x + col_w*(i+1), y+spacing))

        # Rows
        for idx,p in enumerate(processes):
            ry = y + spacing*(idx+1)
            bg = (230,230,230) if idx%2==0 else (245,245,245)
            pygame.draw.rect(screen, bg, (x, ry, table_w, spacing))
            vals = [
                str(p.pid),
                f"{p.arrival_time:.1f}",
                f"{p.burst_time:.1f}",
                f"{p.deadline:.1f}" if p.deadline is not None else "-"
            ]
            for i,val in enumerate(vals):
                cx = x + col_w*i + col_w/2
                cy = ry + spacing/2
                txt = self.font.load().render(val, True, (0,0,0))
                screen.blit(txt, txt.get_rect(center=(cx,cy)))
                pygame.draw.line(screen, (180,180,180),
                                 (x + col_w*(i+1), ry),
                                 (x + col_w*(i+1), ry+spacing))
            # bottom border
            pygame.draw.line(screen, (180,180,180),
                             (x, ry+spacing),
                             (x+table_w, ry+spacing))

    def get_height(self):
        """Header + N rows at last spacing."""
        return (1 + self._last_rows) * self._last_spacing

    def get_width(self):
        """Width used (screen_width minus left & right margins)."""
        return self.screen_width - 2 * self._last_margin_x
