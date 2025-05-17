import pygame

class Table:
    def __init__(self, screen_width, screen_height, font):
        self.screen_width    = screen_width
        self.screen_height   = screen_height
        self.font            = font
        self._last_rows      = 0
        self._last_spacing   = 0
        self._last_margin_x  = 0
        self.see_all_rect    = None

    def draw(self, screen, x, y, cols, processes, spacing=30, truncate=5):
        """
        Render a table of processes at (x, y).

        Parameters:
            screen    – Pygame surface
            x, y      – top-left position
            cols      – list of column headers, e.g. ["PID", "Arrival", "Burst", "Period", "Deadline"]
            processes – list of Process objects
            spacing   – row height in pixels
            truncate  – if set and len(processes) > truncate, show only the first `truncate` rows + a "See all table" link
        """
        # Determine rows to show
        rows_to_show = processes
        if truncate and len(processes) > truncate:
            rows_to_show = processes[:truncate]
        self._last_rows      = len(rows_to_show)
        self._last_spacing   = spacing
        self._last_margin_x  = x

        table_w = self.screen_width - 2 * x
        n_cols  = len(cols)
        col_w   = table_w / n_cols

        # Header row
        hdr_rect = pygame.Rect(x, y, table_w, spacing)
        pygame.draw.rect(screen, (200,200,200), hdr_rect)
        for i, heading in enumerate(cols):
            cx = x + col_w * i + col_w / 2
            cy = y + spacing / 2
            txt = self.font.load().render(heading, True, (0,0,0))
            screen.blit(txt, txt.get_rect(center=(cx, cy)))
            pygame.draw.line(screen, (0,0,0),
                             (x + col_w * (i+1), y),
                             (x + col_w * (i+1), y + spacing))

        # Data rows
        for idx, p in enumerate(rows_to_show):
            ry = y + spacing * (idx + 1)
            bg = (230,230,230) if idx % 2 == 0 else (245,245,245)
            pygame.draw.rect(screen, bg, (x, ry, table_w, spacing))

            vals = []
            for heading in cols:
                key = heading.strip().lower()
                if key in ("#", "pid"):
                    vals.append(str(p.pid))
                elif key in ("arrival", "arrival time"):
                    vals.append(f"{p.arrival_time:.1f}")
                elif key in ("burst", "burst time"):
                    vals.append(f"{p.burst_time:.1f}")
                elif key == "period":
                    vals.append(f"{p.period:.1f}" if p.period is not None else "-")
                elif key == "deadline":
                    vals.append(f"{p.deadline:.1f}" if p.deadline is not None else "-")
                else:
                    vals.append("-")

            for i, val in enumerate(vals):
                cx = x + col_w * i + col_w / 2
                cy = ry + spacing / 2
                txt = self.font.load().render(val, True, (0,0,0))
                screen.blit(txt, txt.get_rect(center=(cx, cy)))
                pygame.draw.line(screen, (180,180,180),
                                 (x + col_w * (i+1), ry),
                                 (x + col_w * (i+1), ry + spacing))
            # bottom border
            pygame.draw.line(screen, (180,180,180),
                             (x, ry + spacing),
                             (x + table_w, ry + spacing))

        # "See all table" link
        if truncate and len(processes) > truncate:
            link_txt = self.font.load().render("See all table", True, (0,0,255))
            link_x   = x + (table_w - link_txt.get_width()) / 2
            link_y   = y + spacing * (truncate + 1) + 10
            self.see_all_rect = link_txt.get_rect(topleft=(link_x, link_y))
            screen.blit(link_txt, self.see_all_rect)
        else:
            self.see_all_rect = None
    def get_height(self):
        h = (1 + self._last_rows) * self._last_spacing
        if self.see_all_rect:
            h += 10 + self.see_all_rect.height
        return h

    def get_width(self):
        return self.screen_width - 2 * self._last_margin_x

    def handle_event(self, event, cols, processes, spacing=30):
        """
        Call this in your event loop. If the user clicks the "See all table" link,
        this opens a new Pygame window showing the full table.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.see_all_rect and self.see_all_rect.collidepoint(event.pos):
                self.show_full_window(cols, processes, spacing)
                
    def show_full_window(self, cols, processes, spacing=30):
        """
        Opens a new Pygame window showing the complete table, with scroll support.
        """
        # Create the new window
        win = pygame.display.set_mode((self.screen_width, self.screen_height))
        scroll_offset = 0
        scroll_speed  = spacing  # scroll one row at a time
        clock = pygame.time.Clock()

        # Pre‐compute full table height
        full_rows = len(processes)
        full_height = (1 + full_rows) * spacing  # header + rows

        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False

                # Mouse wheel
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 4:  # wheel up
                        scroll_offset = min(scroll_offset + scroll_speed, 0)
                    elif ev.button == 5:  # wheel down
                        min_offset = self.screen_height - 50 - full_height
                        scroll_offset = max(scroll_offset - scroll_speed, min_offset)

                # Arrow keys
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_UP:
                        scroll_offset = min(scroll_offset + scroll_speed, 0)
                    elif ev.key == pygame.K_DOWN:
                        min_offset = self.screen_height - 50 - full_height
                        scroll_offset = max(scroll_offset - scroll_speed, min_offset)

            win.fill((240,240,240))

            # Draw full table at y = 50 + scroll_offset
            self.draw(
                screen   = win,
                x        = self._last_margin_x,
                y        = 50 + scroll_offset,
                cols     = cols,
                processes= processes,
                spacing  = spacing,
                truncate = None  # no truncation
            )

            pygame.display.flip()
            clock.tick(60)

        pygame.display.set_mode((self.screen_width, self.screen_height))
