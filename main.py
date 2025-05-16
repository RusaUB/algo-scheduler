import pygame
import sys

from algorithms.process import Process
from algorithms.fcfs import FCFS_Scheduler
from algorithms.sjns import ShortestJobNextScheduler
from algorithms.rrs import RoundRobinScheduler
from algorithms.rms import RateMonotonicScheduler
from algorithms.dfs import DeadlineFirstScheduler
from algorithms.utils import *

from ui.fonts import Font
from ui.cards import Card

class TextInputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.txt_surface = pygame.font.Font(None, 24).render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        elif event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    text = self.text
                    self.text = ''
                    self.txt_surface = pygame.font.Font(None, 24).render(self.text, True, self.color)
                    return text
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = pygame.font.Font(None, 24).render(self.text, True, self.color)
        return None

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

class SchedulerApp:
    def __init__(self, width=900, height=700):
        pygame.init()

        # font init
        pygame.font.init()
        self.font = Font(path="Inter")

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Scheduling Simulator (Pygame)")
        self.clock = pygame.time.Clock()
        # States: "menu", "input", "simulation", "replay"
        self.state = "menu"
        self.process_mode = "random"  # "random" or "custom"
        self.selected_algo = None
        self.scheduler = None
        self.processes = []
        # For custom input using separate boxes.
        self.custom_inputs = []  # list of (arrival, burst, deadline)
        self.arrival_box = TextInputBox(50, 150, 100, 32)
        self.burst_box = TextInputBox(200, 150, 100, 32)
        self.deadline_box = TextInputBox(350, 150, 100, 32)
        # For replay animation.
        self.replaying = False
        self.replay_start_time = None
        self.replay_duration = 5000  # 5 seconds

        # Parameters
        titles      = [
            ("FCFS",           "First-Come, First-Served",      (254,208,125)),
            ("SJN",            "Shortest Job Next",             (255,165,126)),
            ("Round Robin",    "Time-sliced rotation",          (231,241,154)),
            ("Rate Monotonic", "Fixed priorities by period",    (190,158,253)),
            ("Deadline First", "Earliest deadline wins",        (3,217,254)),
        ]
        self.card_w, self.card_h   = 240, 260
        padding_x, padding_y = 30, 20
        start_x, start_y = 50, 50

        self.algo_buttons = []
        for idx, (title, desc, color) in enumerate(titles):
            # row 0: idx 0,1,2 → cols 0,1,2
            # row 1: idx 3,4   → cols 0,1
            row = idx // 3
            col = idx % 3
            # on row 1 we only want 2 columns, but since idx runs 3→row1,col0 and 4→row1,col1,
            # the mod logic works out.
            x = start_x + col * (self.card_w + padding_x)
            y = start_y + row * (self.card_h + padding_y)
            self.algo_buttons.append(
                Card(
                    x, y, self.card_w, self.card_h,
                    title=title,
                    description=desc,
                    title_font=self.font.load(type="SemiBold"),
                    desc_font=self.font.load(type="Light"),
                    bg_color=color
                )
            )


        self.algo_map = {
            "FCFS": "FCFS",
            "SJN":  "SJN",
            "Round Robin": "RR",
            "Rate Monotonic": "RM",
            "Deadline First": "DF",
        }

        # Mode toggle buttons.
        self.mode_buttons = [
            {"label": "Random", "mode": "random", "rect": pygame.Rect(50, 20, 120, 30)},
            {"label": "Custom", "mode": "custom", "rect": pygame.Rect(200, 20, 120, 30)},
        ]
        # Buttons in custom input state.
        self.add_button = {"label": "Add Process", "rect": pygame.Rect(500, 150, 150, 32)}
        self.start_sim_button = {"label": "Start Simulation", "rect": pygame.Rect(500, 200, 200, 40)}
        # In simulation state.
        self.replay_button = {"label": "Replay", "rect": pygame.Rect(50, 600, 120, 40)}
        self.compare_button = {"label": "Compare Metrics", "rect": pygame.Rect(200, 550, 200, 40)}
        self.back_button = {"label": "Back to Menu", "rect": pygame.Rect(200, 600, 150, 40)}

    def run(self):
        running = True
        while running:
            self.screen.fill((240,240,240))
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if self.state == "menu":
                    self.handle_menu_event(event)
                elif self.state == "input":
                    self.handle_input_event(event)
                elif self.state in ("simulation", "replay"):
                    self.handle_simulation_event(event)
                elif self.state == "compare":
                    self.handle_comparison_event(event)  
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "input":
                self.draw_input_screen()
            elif self.state == "simulation":
                self.draw_simulation()
            elif self.state == "compare":
                self.draw_comparison()
            elif self.state == "replay":
                self.draw_replay()

            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()
        sys.exit()

    def handle_comparison_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button["rect"].collidepoint(event.pos):
                self.state = "simulation"


    def handle_menu_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Algorithm cards
            for card in self.algo_buttons:
                if card.rect.collidepoint(pos):
                    label = card.title
                    self.selected_algo = self.algo_map[label]
                    if self.process_mode == "random":
                        include_deadline = self.selected_algo in ("RM", "DF")
                        self.processes = generate_random_processes(5, include_deadline=include_deadline)
                        self.initialize_scheduler()
                        self.scheduler.schedule()
                        self.state = "simulation"
                    else:
                        # No need to reset selected_algo again—just switch to custom input mode
                        self.custom_inputs = []
                        self.processes = []
                        self.state = "input"
                    return  # good practice to bail out once handled

            # Mode buttons (same as before)
            for btn in self.mode_buttons:
                if btn["rect"].collidepoint(pos):
                    self.process_mode = btn["mode"]

    def handle_input_event(self, event):
        # Handle events for each text input box.
        self.arrival_box.handle_event(event)
        self.burst_box.handle_event(event)
        if self.selected_algo in ("RM", "DF"):
            self.deadline_box.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.add_button["rect"].collidepoint(pos):
                try:
                    arrival = float(self.arrival_box.text)
                    burst = float(self.burst_box.text)
                    deadline = None
                    if self.selected_algo in ("RM", "DF"):
                        deadline = float(self.deadline_box.text) if self.deadline_box.text.strip() != "" else arrival + burst + 3
                    self.custom_inputs.append((arrival, burst, deadline))
                    self.arrival_box.text = ""
                    self.burst_box.text = ""
                    self.deadline_box.text = ""
                    self.arrival_box.txt_surface = pygame.font.Font(None, 24).render("", True, self.arrival_box.color)
                    self.burst_box.txt_surface = pygame.font.Font(None, 24).render("", True, self.burst_box.color)
                    self.deadline_box.txt_surface = pygame.font.Font(None, 24).render("", True, self.deadline_box.color)
                except Exception as e:
                    print("Invalid input! Please enter valid numbers.")
            if self.start_sim_button["rect"].collidepoint(pos):
                self.processes = []
                pid = 1
                for (arrival, burst, deadline) in self.custom_inputs:
                    self.processes.append(Process(pid, arrival, burst, deadline))
                    pid += 1
                if not self.processes:
                    print("No processes entered!")
                    return
                self.initialize_scheduler()
                self.scheduler.schedule()
                self.state = "simulation"
            if self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
                self.custom_inputs = []

    def handle_simulation_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.replay_button["rect"].collidepoint(pos):
                self.state = "replay"
                self.replaying = True
                self.replay_start_time = pygame.time.get_ticks()
            elif self.compare_button["rect"].collidepoint(pos):
                self.state = "compare"
            elif self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
                self.process_mode = "random"
                self.selected_algo = None
                self.scheduler = None
                self.processes = []
                self.custom_inputs = []
                self.replaying = False
                
    def draw_comparison(self):
        # Clear background
        self.screen.fill((240,240,240))

        # Title
        title = self.font.load().render("Comparison: Avg Waiting & Turnaround Times", True, (0,0,0))
        self.screen.blit(title, (50, 10))

        # Show process table without metrics
        self.draw_results(
            processes=self.processes,
            chart_top=10,
            chart_height=10,
            left_margin=50,
            right_margin=50,
            show_metrics=False
        )

        # --- Compute metrics for each algorithm ---
        labels = ["FCFS", "SJN", "RR", "RM", "DF"]
        ctors  = [
            FCFS_Scheduler,
            ShortestJobNextScheduler,
            lambda: RoundRobinScheduler(time_quantum=2),
            RateMonotonicScheduler,
            DeadlineFirstScheduler
        ]
        wait_times = []
        turn_times = []
        for lbl, ctor in zip(labels, ctors):
            sched = ctor()
            for orig in self.processes:
                arrival, burst, dead = orig.arrival_time, orig.burst_time, orig.deadline
                if lbl in ("RM", "DF") and dead is None:
                    dead = arrival + burst + 3
                sched.add_process(Process(orig.pid, arrival, burst, dead))
            sched.schedule()
            wait_times.append(sched.average_waiting_time())
            turn_times.append(sched.average_turnaround_time())

        # --- Draw bar chart ---
        chart_x      = 50
        chart_y      = 300
        chart_width  = self.width - 100
        chart_height = 200
        n            = len(labels)
        spacing_grp  = 20
        group_w      = (chart_width - spacing_grp * (n + 1)) / n
        bar_w        = group_w / 2
        max_val      = max(max(wait_times), max(turn_times), 1)

        # Axes
        pygame.draw.line(self.screen, (0,0,0),
                        (chart_x, chart_y + chart_height),
                        (chart_x + chart_width, chart_y + chart_height), 2)
        pygame.draw.line(self.screen, (0,0,0),
                        (chart_x, chart_y),
                        (chart_x, chart_y + chart_height), 2)

        # Y-axis tick labels & grid lines
        num_yticks = 5
        for i in range(num_yticks + 1):
            val = max_val * i / num_yticks
            y   = chart_y + chart_height - (i / num_yticks) * chart_height
            lbl = self.font.load().render(f"{val:.1f}", True, (0,0,0))
            self.screen.blit(lbl, (chart_x - lbl.get_width() - 10, y - lbl.get_height()/2))
            pygame.draw.line(self.screen, (200,200,200),
                            (chart_x, y),
                            (chart_x + chart_width, y), 1)

        # Bars + x-labels
        for i, lbl in enumerate(labels):
            base_x = chart_x + spacing_grp + i * (group_w + spacing_grp)
            # Waiting time bar (left)
            h_w = (wait_times[i] / max_val) * chart_height
            rect_w = pygame.Rect(base_x,
                                chart_y + chart_height - h_w,
                                bar_w,
                                h_w)
            pygame.draw.rect(self.screen, (254,90,90), rect_w)
            # Turnaround time bar (right)
            h_t = (turn_times[i] / max_val) * chart_height
            rect_t = pygame.Rect(base_x + bar_w,
                                chart_y + chart_height - h_t,
                                bar_w,
                                h_t)
            pygame.draw.rect(self.screen, (90,180,254), rect_t)

            # Algorithm label under group
            lbl_surf = self.font.load().render(lbl, True, (0,0,0))
            lbl_rect = lbl_surf.get_rect(
                center=(base_x + group_w/2, chart_y + chart_height + 20)
            )
            self.screen.blit(lbl_surf, lbl_rect)

        # --- Legend (centered between bar clusters) ---
        lw_surf = self.font.load().render("Avg Waiting", True, (254,90,90))
        lt_surf = self.font.load().render("Avg Turnaround", True, (90,180,254))
        spacing_leg = 40
        total_leg_w = lw_surf.get_width() + spacing_leg + lt_surf.get_width()
        legend_x = chart_x + (chart_width - total_leg_w) / 2
        legend_y = chart_y + chart_height + 50
        # Waiting legend
        self.screen.blit(lw_surf, (legend_x, legend_y))
        # Turnaround legend
        self.screen.blit(lt_surf, (legend_x + lw_surf.get_width() + spacing_leg, legend_y))

        # --- Back button at left margin ---
        left_margin = 50
        btn_y = self.back_button["rect"].y
        self.back_button["rect"].topleft = (left_margin, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_txt = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(back_txt, back_txt.get_rect(center=self.back_button["rect"].center))


    def draw_menu(self):
        # 1) Main title at top‐left
        title_surf = self.font.load(size="md", type="Black").render("Scheduling Simulator - Menu", True, (0, 0, 0))
        self.screen.blit(title_surf, (50, 10))

        # 2) “Select Process Mode:” label at left + buttons at right, same row
        controls_y = 70
        label_surf = self.font.load().render("Select Process Mode:", True, (0, 0, 0))
        self.screen.blit(label_surf, (50, controls_y))

        # compute right‐aligned buttons in a flex row
        btn_w, btn_h = self.mode_buttons[0]["rect"].size
        spacing      = 10
        margin       = 20
        total_btns_w = len(self.mode_buttons) * btn_w + (len(self.mode_buttons) - 1) * spacing
        x            = self.width - margin - total_btns_w

        for btn in self.mode_buttons:
            # choose colors based on active state
            if btn["mode"] == self.process_mode:
                bg, fg = (0,0,0), (255,255,255)
            else:
                bg, fg = (200,200,200), (0,0,0)
            btn["rect"].topleft = (x, controls_y)
            pygame.draw.rect(self.screen, bg, btn["rect"])
            txt_surf = self.font.load().render(btn["label"], True, fg)
            txt_rect = txt_surf.get_rect(center=btn["rect"].center)
            self.screen.blit(txt_surf, txt_rect)
            x += btn_w + spacing

        # 3) Now draw the algorithm cards *below* the controls (no overlay)
        for card in self.algo_buttons:
            card.draw(self.screen)


    def draw_input_screen(self):
        title = self.font.load().render("Custom Process Input", True, (0,0,0))
        self.screen.blit(title, (50,50))
        # Draw labels and input boxes for each parameter.
        arrival_label = self.font.load().render("Arrival Time:", True, (0,0,0))
        self.screen.blit(arrival_label, (50,120))
        self.arrival_box.draw(self.screen)

        burst_label = self.font.load().render("Burst Time:", True, (0,0,0))
        self.screen.blit(burst_label, (200,120))
        self.burst_box.draw(self.screen)

        if self.selected_algo in ("RM", "DF"):
            deadline_label = self.font.load().render("Deadline:", True, (0,0,0))
            self.screen.blit(deadline_label, (350,120))
            self.deadline_box.draw(self.screen)

        pygame.draw.rect(self.screen, (50,150,50), self.add_button["rect"])
        add_text = self.font.load().render(self.add_button["label"], True, (255,255,255))
        self.screen.blit(add_text, self.add_button["rect"].move(5,5))
        y = 220
        list_title = self.font.load().render("Processes Added:", True, (0,0,0))
        self.screen.blit(list_title, (50,y))
        y += 30
        for idx, proc in enumerate(self.custom_inputs):
            proc_text = f"{idx+1}: Arrival={proc[0]}, Burst={proc[1]}" + (f", Deadline={proc[2]}" if proc[2] is not None else "")
            line = self.font.load().render(proc_text, True, (0,0,0))
            self.screen.blit(line, (50,y))
            y += 30
        pygame.draw.rect(self.screen, (200,50,50), self.start_sim_button["rect"])
        start_text = self.font.load().render(self.start_sim_button["label"], True, (255,255,255))
        self.screen.blit(start_text, self.start_sim_button["rect"].move(5,5))
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_text = self.font.load().render("Back", True, (255,255,255))
        self.screen.blit(back_text, self.back_button["rect"].move(10,5))

    def draw_results(self, processes, chart_top, chart_height, left_margin, right_margin, show_metrics = True):
        # ─── Processes Table (full‐width) ───────────────────────────────────────────────
        table_x = left_margin
        table_width = self.width - left_margin - right_margin
        row_h =  thirty = 30
        cols = ["PID", "Arrival", "Burst", "Deadline"]
        n_cols = len(cols)
        col_w = table_width / n_cols
        # Header row
        hdr_rect = pygame.Rect(table_x, chart_top + chart_height + 50, table_width, row_h)
        pygame.draw.rect(self.screen, (200,200,200), hdr_rect)
        for i, h in enumerate(cols):
            cx = table_x + col_w * i + col_w/2
            cy = hdr_rect.y + row_h/2
            txt = self.font.load().render(h, True, (0,0,0))
            self.screen.blit(txt, txt.get_rect(center=(cx,cy)))
            # vertical divider
            pygame.draw.line(self.screen, (0,0,0),
                            (table_x + col_w*(i+1), hdr_rect.y),
                            (table_x + col_w*(i+1), hdr_rect.y + row_h))
        # Rows
        for idx, p in enumerate(processes):
            y = hdr_rect.y + row_h*(idx+1)
            bg = (230,230,230) if idx%2==0 else (245,245,245)
            pygame.draw.rect(self.screen, bg, (table_x, y, table_width, row_h))
            cells = [
                str(p.pid),
                f"{p.arrival_time:.1f}",
                f"{p.burst_time:.1f}",
                f"{p.deadline:.1f}" if p.deadline is not None else "-"
            ]
            for i, val in enumerate(cells):
                cx = table_x + col_w * i + col_w/2
                cy = y + row_h/2
                txt = self.font.load().render(val, True, (0,0,0))
                self.screen.blit(txt, txt.get_rect(center=(cx,cy)))
                pygame.draw.line(self.screen, (180,180,180),
                                (table_x + col_w*(i+1), y),
                                (table_x + col_w*(i+1), y + row_h))
            pygame.draw.line(self.screen, (180,180,180),
                            (table_x, y+row_h),
                            (table_x + table_width, y+row_h))
            
        if show_metrics:    
            # ─── Average Metrics ───────────────────────────────────────────────────────────
            base_y = hdr_rect.y + row_h * (len(self.processes) + 2)
            avg_wt  = self.scheduler.average_waiting_time()
            avg_tat = self.scheduler.average_turnaround_time()
            wt_txt  = self.font.load().render(f"Avg waiting time: {avg_wt:.2f}", True, (0,0,0))
            tat_txt = self.font.load().render(f"Avg turnaround time: {avg_tat:.2f}", True, (0,0,0))
            self.screen.blit(wt_txt,  (table_x, base_y))
            self.screen.blit(tat_txt, (table_x, base_y + row_h))
    
    def draw_simulation(self):
        title = self.font.load().render("Simulation Result", True, (0,0,0))
        self.screen.blit(title, (50,10))
        if not self.scheduler or not self.scheduler.timeline:
            return

        # ─── Gantt Chart ───────────────────────────────────────────────────────────────
        start_time = min(seg[1] for seg in self.scheduler.timeline)
        end_time   = max(seg[2] for seg in self.scheduler.timeline)
        total_time = max(end_time - start_time, 1)
        chart_top    = 150
        chart_height = 100
        chart_left   = 50
        chart_width  = self.width - 100

        pygame.draw.line(self.screen, (0,0,0),
                        (chart_left, chart_top+chart_height),
                        (chart_left+chart_width, chart_top+chart_height), 2)
        for pid, s, e in self.scheduler.timeline:
            x = chart_left + ((s - start_time) / total_time) * chart_width
            w = ((e - s) / total_time) * chart_width
            rect = pygame.Rect(x, chart_top, w, chart_height)
            pygame.draw.rect(self.screen, (100,180,100), rect)
            pygame.draw.line(self.screen, (0,0,0),
                            (x+w, chart_top),
                            (x+w, chart_top+chart_height), 2)
            lbl = self.font.load().render(f"P{pid}", True, (255,255,255))
            self.screen.blit(lbl, rect.move(5,5))
        for i in range(7):
            t = start_time + i * (total_time/6)
            xm = chart_left + ((t - start_time)/total_time) * chart_width
            mark = self.font.load().render(f"{t:.1f}", True, (0,0,0))
            self.screen.blit(mark, (xm-10, chart_top+chart_height+5))

        left_margin = 50
        right_margin = 50
        self.draw_results(processes=self.processes, chart_height=chart_height, chart_top=chart_top, left_margin=left_margin, right_margin=right_margin)

        # ─── Buttons ───────────────────────────────────────────────────────────────────
        # Back at left margin
        btn_y = self.back_button["rect"].y
        self.back_button["rect"].topleft = (left_margin, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        bl = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(bl, bl.get_rect(center=self.back_button["rect"].center))

        # Compare & Replay right-aligned
        spacing = 10
        right_btns = [(self.compare_button,(200,100,50)),
                    (self.replay_button,(50,50,200))]
        total_w = sum(b["rect"].width for b,_ in right_btns) + spacing*(len(right_btns)-1)
        x = self.width - right_margin - total_w
        for btn, color in right_btns:
            btn["rect"].topleft = (x, btn_y)
            pygame.draw.rect(self.screen, color, btn["rect"])
            txt = self.font.load().render(btn["label"], True, (255,255,255))
            self.screen.blit(txt, txt.get_rect(center=btn["rect"].center))
            x += btn["rect"].width + spacing

    def draw_replay(self):
        if not self.scheduler or not self.scheduler.timeline:
            return

        # 1) Draw the same background & static UI that draw_simulation does:
        # -----------------------------------------------------------------
        # Title
        title = self.font.load().render("Simulation Result (Replay)", True, (0,0,0))
        self.screen.blit(title, (50,10))

        # Compute chart geometry
        start_time = min(seg[1] for seg in self.scheduler.timeline)
        end_time   = max(seg[2] for seg in self.scheduler.timeline)
        total_time = end_time - start_time if end_time != start_time else 1
        chart_top    = 150
        chart_height = 100
        chart_left   = 50
        chart_width  = self.width - 100

        # Draw x-axis
        pygame.draw.line(self.screen, (0,0,0),
                         (chart_left, chart_top+chart_height),
                         (chart_left+chart_width, chart_top+chart_height), 2)

        # Draw time markers
        num_markers = 6
        for i in range(num_markers+1):
            t = start_time + i * (total_time/num_markers)
            x = chart_left + ((t - start_time) / total_time) * chart_width
            time_label = self.font.load().render(f"{t:.1f}", True, (0,0,0))
            self.screen.blit(time_label, (x-10, chart_top+chart_height+5))

        # Draw the process list (for random mode)
        if self.process_mode == "random":
            proc_title = self.font.load().render("Random Processes:", True, (0,0,0))
            self.screen.blit(proc_title, (50, chart_top+chart_height+50))
            y = chart_top+chart_height+80
            self.draw_results(processes=self.processes, chart_top=chart_top, chart_height=chart_height, left_margin=50, right_margin=50)

        # Draw your static buttons
        pygame.draw.rect(self.screen, (50,50,200), self.replay_button["rect"])
        rep_text = self.font.load().render(self.replay_button["label"], True, (255,255,255))
        self.screen.blit(rep_text, self.replay_button["rect"].move(5,5))

        pygame.draw.rect(self.screen, (200,100,50), self.compare_button["rect"])
        cmp_text = self.font.load().render(self.compare_button["label"], True, (255,255,255))
        self.screen.blit(cmp_text, self.compare_button["rect"].move(5,5))

        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_text = self.font.load().render("Back", True, (255,255,255))
        self.screen.blit(back_text, self.back_button["rect"].move(10,5))

        # 2) Now draw the animated bars *on top*:
        # -----------------------------------------
        now     = pygame.time.get_ticks()
        elapsed = now - self.replay_start_time
        progress = min(elapsed / self.replay_duration, 1.0)

        for seg in self.scheduler.timeline:
            pid, seg_start, seg_end = seg
            norm_start = (seg_start - start_time) / total_time
            norm_end   = (seg_end   - start_time) / total_time

            if progress >= norm_start:
                portion = min(1.0,
                              (progress - norm_start) / (norm_end - norm_start)
                              if (norm_end - norm_start) > 0 else 1)
                x0 = chart_left + norm_start * chart_width
                full_w = (norm_end - norm_start) * chart_width
                cur_w = full_w * portion

                rect = pygame.Rect(x0, chart_top, cur_w, chart_height)
                pygame.draw.rect(self.screen, (100,180,100), rect)

                if progress >= norm_end:
                    # finalize the divider if fully done
                    pygame.draw.line(self.screen, (0,0,0),
                                     (x0+full_w, chart_top),
                                     (x0+full_w, chart_top+chart_height), 2)

                # label
                label = self.font.load().render(f"P{pid}", True, (255,255,255))
                self.screen.blit(label, rect.move(5,5))
                
    def initialize_scheduler(self):
        if self.selected_algo == "FCFS":
            self.scheduler = FCFS_Scheduler()
        elif self.selected_algo == "SJN":
            self.scheduler = ShortestJobNextScheduler()
        elif self.selected_algo == "RR":
            self.scheduler = RoundRobinScheduler(time_quantum=2)
        elif self.selected_algo == "RM":
            self.scheduler = RateMonotonicScheduler()
        elif self.selected_algo == "DF":
            self.scheduler = DeadlineFirstScheduler()
        if self.scheduler:
            for p in self.processes:
                self.scheduler.add_process(p)

def main_pygame():
    app = SchedulerApp()
    app.run()

# ---------------------------
# Command Line Interface (unchanged)
# ---------------------------
def main_cli():
    print("Welcome to the Scheduling Simulator Base (CLI)")
    print("Algorithms available:")
    print("1. First-Come-First-Served (FCFS)")
    print("2. Shortest Job Next (SJN)")
    print("3. Round Robin (RR)")
    print("4. Rate Monotonic (RM)")
    print("5. Deadline First (DF)")
    
    algo_choice = input("Enter algorithm choice (1-5): ").strip()
    
    scheduler = None
    if algo_choice == "1":
        scheduler = FCFS_Scheduler()
    elif algo_choice == "2":
        scheduler = ShortestJobNextScheduler()
    elif algo_choice == "3":
        try:
            tq = int(input("Enter time quantum for Round Robin scheduling: "))
        except ValueError:
            tq = 2
            print("Invalid input. Defaulting time quantum to 2.")
        scheduler = RoundRobinScheduler(tq)
    elif algo_choice == "4":
        scheduler = RateMonotonicScheduler()
    elif algo_choice == "5":
        scheduler = DeadlineFirstScheduler()
    else:
        print("Invalid choice. Exiting simulation.")
        return

    user_option = input("Would you like to manually input process parameters? (y/n): ").strip().lower()
    processes = []
    if user_option == "y":
        try:
            num = int(input("Enter number of processes: "))
        except ValueError:
            num = 3
            print("Invalid input. Defaulting to 3 processes.")
        for i in range(num):
            print(f"\nProcess {i+1}:")
            try:
                arrival = int(input("  Arrival time: "))
                burst = int(input("  Burst time: "))
            except ValueError:
                print("  Invalid input. Using default values (arrival: 0, burst: 5).")
                arrival, burst = 0, 5
            deadline = None
            if algo_choice in ("4", "5"):
                try:
                    deadline = int(input("  Deadline: "))
                except ValueError:
                    deadline = arrival + burst + 3
                    print("  Invalid input. Using default deadline (arrival + burst + 3).")
            processes.append(Process(pid=i+1, arrival_time=arrival, burst_time=burst, deadline=deadline))
    else:
        try:
            num = int(input("Enter number of processes to generate randomly: "))
        except ValueError:
            num = 3
            print("Invalid input. Defaulting to 3 processes.")
        include_deadline = (algo_choice in ("4", "5"))
        processes = generate_random_processes(num, include_deadline=include_deadline)
    
    print("\nProcesses:")
    display_process_info(processes)
    
    for process in processes:
        scheduler.add_process(process)
    scheduler.schedule()
    
    print("\nScheduling Timeline (ASCII Gantt Chart):")
    scheduler.print_timeline()
    
    plot_option = input("Would you like to view a graphical Gantt chart (matplotlib)? (y/n): ").strip().lower()
    if plot_option == "y":
        scheduler.plot_gantt_chart()

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    print("Choose interface:")
    print("1. Command Line Interface (CLI)")
    print("2. Pygame Interface")
    choice = input("Enter 1 or 2: ").strip()
    if choice == "1":
        main_cli()
    else:
        main_pygame()