import pygame

class BarChart:
    def __init__(
        self,
        labels,
        wait_times,
        turn_times,
        x,
        y,
        width,
        height,
        bar_colors=((254, 90, 90), (90, 180, 254)),
        marker_count=0,
        zoomed=False
    ):
        """
        labels       – list of algorithm names
        wait_times   – list of avg waiting times
        turn_times   – list of avg turnaround times
        x, y         – top-left origin of the chart
        width        – total width for all bars + spacing
        height       – bar area height (excluding space for labels)
        bar_colors   – tuple of two RGB tuples: (waiting_color, turnaround_color)
        marker_count – number of Y-axis grid lines (0 = none)
        zoomed       – if True, scale bars by the max of the first three algos only
        """
        self.labels       = labels
        self.wait_times   = wait_times
        self.turn_times   = turn_times
        self.x            = x
        self.y            = y
        self.width        = width
        self.height       = height
        self.wait_col, self.turn_col = bar_colors
        self.marker_count = marker_count
        self.zoomed       = zoomed

        # space below bars for algorithm labels
        self._label_space  = 30
        # space above bars for legend
        self._legend_space = 30

    def draw(self, screen, font):
        # ─── Legend ────────────────────────────────────────────────────────────────
        legend_y   = self.y - self._legend_space
        swatch_sz  = 12
        gap        = 5

        # Avg Waiting legend
        lw_surf = font.load().render("Avg Waiting", True, (0,0,0))
        sw1     = pygame.Rect(
            self.x,
            legend_y + (self._legend_space - swatch_sz)//2,
            swatch_sz, swatch_sz
        )
        pygame.draw.rect(screen, self.wait_col, sw1)
        screen.blit(lw_surf, (self.x + swatch_sz + gap, legend_y))

        # Avg Turnaround legend
        lt_surf = font.load().render("Avg Turnaround", True, (0,0,0))
        x2      = (
            self.x
            + swatch_sz + gap
            + lw_surf.get_width()
            + 40
        )
        sw2     = pygame.Rect(
            x2,
            legend_y + (self._legend_space - swatch_sz)//2,
            swatch_sz, swatch_sz
        )
        pygame.draw.rect(screen, self.turn_col, sw2)
        screen.blit(lt_surf, (x2 + swatch_sz + gap, legend_y))

        # ─── Y-axis grid & ticks ───────────────────────────────────────────────────
        if self.marker_count > 0:
            # compute global max over all algos
            global_max = max(
                max(self.wait_times, default=0),
                max(self.turn_times, default=0),
                1
            )
            # compute zoomed max over first 3 algos
            subset_max = max(
                max(self.wait_times[:3], default=0),
                max(self.turn_times[:3], default=0),
                1
            )
            max_val = subset_max if self.zoomed else global_max

            for i in range(self.marker_count+1):
                frac = i / self.marker_count
                y    = self.y + self.height * (1 - frac)
                pygame.draw.line(
                    screen, (200,200,200),
                    (self.x, y),
                    (self.x + self.width, y),
                    1
                )
                val = max_val * frac
                lbl = font.load().render(f"{val:.1f}", True, (0,0,0))
                screen.blit(
                    lbl,
                    (self.x - lbl.get_width() - 5,
                     y - lbl.get_height()/2)
                )

        # ─── Bars + X-labels ────────────────────────────────────────────────────────
        n          = len(self.labels)
        spacing_grp = 20
        group_w     = (self.width - spacing_grp*(n+1)) / n
        bar_w       = group_w / 2

        # again compute max for bar heights
        global_max = max(
            max(self.wait_times, default=0),
            max(self.turn_times, default=0),
            1
        )
        subset_max = max(
            max(self.wait_times[:3], default=0),
            max(self.turn_times[:3], default=0),
            1
        )
        max_val = subset_max if self.zoomed else global_max

        for i, lbl in enumerate(self.labels):
            base_x = self.x + spacing_grp + i*(group_w + spacing_grp)

            # waiting bar
            val_w     = self.wait_times[i]
            # clamp to max_val
            clamped_w = min(val_w, max_val)
            h_w       = (clamped_w / max_val) * self.height
            rect_w    = pygame.Rect(
                base_x,
                self.y + self.height - h_w,
                bar_w, h_w
            )
            pygame.draw.rect(screen, self.wait_col, rect_w)

            # turnaround bar
            val_t     = self.turn_times[i]
            clamped_t = min(val_t, max_val)
            h_t       = (clamped_t / max_val) * self.height
            rect_t    = pygame.Rect(
                base_x + bar_w,
                self.y + self.height - h_t,
                bar_w, h_t
            )
            pygame.draw.rect(screen, self.turn_col, rect_t)

            # algorithm label
            lbl_surf = font.load().render(lbl, True, (0,0,0))
            lbl_rect = lbl_surf.get_rect(
                center=(
                    base_x + group_w/2,
                    self.y + self.height + self._label_space/2
                )
            )
            screen.blit(lbl_surf, lbl_rect)

    def get_width(self):
        return self.width

    def get_height(self):
        # total height = legend + bars + label space
        return self._legend_space + self.height + self._label_space
