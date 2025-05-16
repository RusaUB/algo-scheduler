import pygame

class GanttChart:
    def __init__(self, x, y, width, height, timeline, process_colors, marker_count=6):
        """
        x, y             — top‐left of the chart area
        width, height    — dimensions of the bar area (not including labels)
        timeline         — list of (pid, start_time, end_time)
        process_colors   — dict mapping pid → (r,g,b)
        marker_count     — number of intervals on the time axis
        """
        self.x              = x
        self.y              = y
        self.width          = width
        self.height         = height
        self.timeline       = timeline
        self.process_colors = process_colors
        self.marker_count   = marker_count
        # reserve extra space below bars for labels
        self._label_space   = 20  

    def draw(self, screen, font):
        if not self.timeline:
            return

        # Compute time range
        start = min(seg[1] for seg in self.timeline)
        end   = max(seg[2] for seg in self.timeline)
        total = max(end - start, 1)

        # Draw x-axis
        axis_y = self.y + self.height
        pygame.draw.line(screen, (0,0,0),
                         (self.x, axis_y),
                         (self.x + self.width, axis_y), 2)

        # Draw bars
        for pid, s, e in self.timeline:
            norm_s = (s - start) / total
            norm_e = (e - start) / total
            px     = self.x + norm_s * self.width
            pw     = (norm_e - norm_s) * self.width
            rect   = pygame.Rect(px, self.y, pw, self.height)
            color  = self.process_colors.get(pid, (100,180,100))
            pygame.draw.rect(screen, color, rect)
            pygame.draw.line(screen, (0,0,0),
                             (px + pw, self.y),
                             (px + pw, self.y + self.height), 2)
            lbl = font.load().render(f"P{pid}", True, (255,255,255))
            screen.blit(lbl, rect.move(5,5))

        # Draw time markers and labels
        for i in range(self.marker_count + 1):
            t = start + i * (total / self.marker_count)
            mx = self.x + (i / self.marker_count) * self.width
            # tick
            pygame.draw.line(screen, (0,0,0),
                             (mx, axis_y),
                             (mx, axis_y + 5), 1)
            # label
            txt = font.load().render(f"{t:.1f}", True, (0,0,0))
            screen.blit(txt, (mx - txt.get_width()/2, axis_y + 5))

    def get_width(self):
        """Total width of the chart area."""
        return self.width

    def get_height(self):
        """Total height: bars plus label space."""
        return self.height + self._label_space
