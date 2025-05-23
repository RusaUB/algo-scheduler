import pygame
import sys

from algorithms.process import Process
from algorithms.fcfs import FCFS_Scheduler
from algorithms.sjns import ShortestJobNextScheduler
from algorithms.rrs import RoundRobinScheduler
from algorithms.rms import RateMonotonicScheduler
from algorithms.dfs import DeadlineFirstScheduler
from algorithms.utils import *

from components.bar_chart import BarChart
from components.gantt_chart import GanttChart
from ui.fonts import Font
from ui.cards import Card

from components.table import Table
from components.container import Container

class TextInputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active   = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text  = text
        self.txt_surface = pygame.font.Font(None, 24).render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color  = self.color_active if self.active else self.color_inactive

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                val = self.text
                self.text = ''
                return val

            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            else:
                ch = event.unicode
                # only accept digit characters
                if ch.isdigit():
                    new_text = self.text + ch
                    # enforce integer ≤ 20
                    try:
                        if 0 <= int(new_text) <= 20:
                            self.text = new_text
                    except ValueError:
                        pass

            # re-render
            self.txt_surface = pygame.font.Font(None, 24).render(self.text, True, self.color)

        return None

    def draw(self, screen, placeholder=''):
        # decide what to render
        if self.text:
            disp = self.text
            col  = self.color
        else:
            disp = placeholder
            col  = pygame.Color('grey')

        # render centered in box
        self.txt_surface = pygame.font.Font(None, 24).render(disp, True, col)
        txt_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, txt_rect)

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
        self.period_box   = TextInputBox(350, 150, 100, 32)

        # For replay animation.
        self.replaying = False
        self.replay_start_time = None
        self.replay_duration = 5000  # 5 seconds

        self.table = Table(self.width, self.height, self.font)
        self.margin_x = 50

        self.MAX_PROCESSES = 8

        self.selected_algo_display = None

        # Parameters
        titles = [
            ("FCFS",
            "First-Come, First-Served\n\nnon-preemptive\nno timing constraints\nno priority",
            (254,208,125)),

            ("SJN",
            "Shortest Job Next\n\nnon-preemptive\nno timing constraints\nno priority",
            (255,165,126)),

            ("Round Robin",
            "Time-sliced rotation\n\npreemptive\nsoft real-time\nno priority",
            (231,241,154)),

            ("Rate Monotonic",
            "Fixed priorities by period\n\npreemptive\nhard real-time\nstatic priority",
            (190,158,253)),

            ("Deadline First",
            "Earliest deadline wins\n\npreemptive\nhard real-time\ndynamic priority",
            (3,217,254)),
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
        self.add_button = {"label": "Add Process", "rect": pygame.Rect(650, 150, 150, 32)}
        self.start_sim_button = {"label": "Start Simulation", "rect": pygame.Rect(500, 200, 200, 40)}
        # In simulation state.
        self.replay_button = {"label": "Replay", "rect": pygame.Rect(50, 600, 120, 40)}
        self.compare_button = {"label": "Compare Metrics", "rect": pygame.Rect(200, 550, 200, 40)}
        self.back_button = {"label": "Back to Menu", "rect": pygame.Rect(200, 600, 150, 40)}

        self.process_colors = {}

        self.comparison_zoomed = False
        self.zoom_button = {
            "rect": pygame.Rect(self.width-80-self.margin_x, 50, 80, 30)
        }

        self.max_hyperperiod    = 100
        self.hyper_auto_btn     = {"label":"Auto Fix","rect":pygame.Rect(self.width-50-120, self.height-50-40, 120,40)}
        self.hyper_manual_btn   = {"label":"Manual","rect":pygame.Rect(self.width-50-120-10-120, self.height-50-40, 120,40)}
 

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
                elif self.state == "hyper_warning":
                    self.handle_hyper_warning_event(event)
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "input":
                self.draw_input_screen()
            elif self.state == "simulation":
                self.draw_simulation()
            elif self.state == "compare":
                self.draw_comparison()
            elif self.state == "hyper_warning":
                self.draw_hyper_warning()
            elif self.state == "replay":
                self.draw_replay()

            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()
        sys.exit()

    def handle_comparison_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.zoom_button["rect"].collidepoint(event.pos):
                self.comparison_zoomed = not self.comparison_zoomed
                return

            # existing “see all table” handler
            self.table.handle_event(
                event,
                cols=["PID","Arrival","Burst","Deadline"],
                processes=self.processes,
                spacing=30
            )

            # back button
            if self.back_button["rect"].collidepoint(event.pos):
                self.state = "simulation"


    def handle_menu_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Algorithm cards
            for card in self.algo_buttons:
                if card.rect.collidepoint(pos):
                    label = card.title
                    self.selected_algo_display = card.title  
                    self.selected_algo = self.algo_map[label]
                    if self.process_mode == "random":
                        # always generate both period & deadline,
                        # so later comparison can hand them off to RM/EDF as needed
                        self.processes = generate_random_processes(
                            5,
                            include_period=True,
                            include_deadline=True
                        )
                        self.initialize_scheduler()
                        self.scheduler.schedule()
                        self.state = "simulation"
                    else:
                        # custom‐input branch
                        self.custom_inputs = []
                        self.processes = []
                        self.state = "input"
                    return

            # Mode buttons
            for btn in self.mode_buttons:
                if btn["rect"].collidepoint(pos):
                    self.process_mode = btn["mode"]

    def handle_input_event(self, event):
        from algorithms.process import Process
        proc_objs = [
            Process(
                pid=idx+1,
                arrival_time=a,
                burst_time=b,
                period=pr,
                deadline=dl
            )
            for idx, (a,b,pr,dl) in enumerate(self.custom_inputs)
        ]
        self.table.handle_event(
            event,
            cols=["#", "Arrival", "Burst", "Period", "Deadline"],
            processes=proc_objs,
            spacing=30
        )

        # Forward events to our text‐boxes
        self.arrival_box.handle_event(event)
        self.burst_box.handle_event(event)
        if self.selected_algo in ("RM", "DF"):
            self.period_box.handle_event(event)
        if self.selected_algo == "DF":
            self.deadline_box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # — Add Process —
            if self.add_button["rect"].collidepoint(pos):
                # enforce maximum
                if len(self.custom_inputs) >= self.MAX_PROCESSES:
                    # optionally flash a warning or ignore
                    print(f"Cannot add more than {self.MAX_PROCESSES} processes")
                    return
                try:
                    # 1) arrival
                    if self.arrival_box.text.strip():
                        arrival = float(self.arrival_box.text)
                    else:
                        # next unused integer
                        used = {int(x[0]) for x in self.custom_inputs}
                        arrival = next(i for i in range(1000) if i not in used)

                    # 2) burst
                    if self.burst_box.text.strip():
                        burst = float(self.burst_box.text)
                    else:
                        burst = random.randint(1, 10)

                    # 3) period (always generate even if this algorithm doesn't use it)
                    if self.period_box.text.strip():
                        period = float(self.period_box.text)
                    else:
                        period = burst + random.randint(1, 10)

                    # 4) deadline
                    if self.deadline_box.text.strip():
                        deadline = float(self.deadline_box.text)
                    else:
                        deadline = arrival + burst + random.randint(0, 5)

                    # store the 4‐tuple
                    self.custom_inputs.append((arrival, burst, period, deadline))

                    # clear the boxes
                    for box in (self.arrival_box, self.burst_box, self.period_box, self.deadline_box):
                        box.text = ""
                        box.txt_surface = pygame.font.Font(None, 24).render("", True, box.color)

                except Exception:
                    print("Invalid input! Please enter numbers.")

            # — Start Simulation —
            elif self.start_sim_button["rect"].collidepoint(pos):
                if self.selected_algo in ("RM","DF"):
                    # gather all periods
                    periods = [pr for (_,_,pr,_) in self.custom_inputs]
                    # simple lcm over list
                    from math import gcd
                    def lcm(a,b): return a*b//gcd(a,b)
                    H = 1
                    for p in periods:
                        H = lcm(H, p)
                    if H > self.max_hyperperiod:
                        # store for the popup
                        self.bad_hyper = H
                        self.n_custom = len(self.custom_inputs)
                        self.state = "hyper_warning"
                        return

            # otherwise fall through to original simulation start
                self.processes = []
                pid = 1
                for a, b, pr, dl in self.custom_inputs:
                    # pass all fields; each algorithm will pick what it needs
                    self.processes.append(Process(
                        pid=pid,
                        arrival_time=a,
                        burst_time=b,
                        deadline=dl,
                        period=pr
                    ))
                    pid += 1

                if not self.processes:
                    print("No processes to simulate!")
                    return

                self.initialize_scheduler()
                self.scheduler.schedule()
                self.state = "simulation"

            # — Back to Menu —
            elif self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
                self.custom_inputs.clear()

    def handle_simulation_event(self, event):
        # First, let the table detect any "See all table" clicks
        self.table.handle_event(
            event,
            cols=["PID", "Arrival", "Burst", "Deadline"],
            processes=self.processes,
            spacing=30
        )

        # Then handle the normal simulation‐state buttons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Replay button
            if self.replay_button["rect"].collidepoint(pos):
                self.state = "replay"
                self.replaying = True
                self.replay_start_time = pygame.time.get_ticks()

            # Compare Metrics button
            elif self.compare_button["rect"].collidepoint(pos):
                self.state = "compare"

            # Back to Menu button
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

        # ─── Zoom toggle ─────────────────────────────────────────────────────────
        lbl = "De-zoom" if self.comparison_zoomed else "Zoom"
        pygame.draw.rect(self.screen, (100,100,100), self.zoom_button["rect"])
        txt = self.font.load().render(lbl, True, (255,255,255))
        self.screen.blit(txt, txt.get_rect(center=self.zoom_button["rect"].center))


        # ─── Truncated Process Table ──────────────────────────────────────────────
        table_x, table_y = 50, 100
        cols    = ["PID", "Arrival", "Burst", "Deadline"]
        self.table.draw(
            screen    = self.screen,
            x         = table_x,
            y         = table_y,
            cols      = cols,
            processes = self.processes,
            spacing   = 30,
            truncate  = 5
        )
        table_h = self.table.get_height()

        # ─── Compute metrics ──────────────────────────────────────────────────────
        labels = ["FCFS","SJN","RR","RM","DF"]
        ctors  = [
            FCFS_Scheduler,
            ShortestJobNextScheduler,
            lambda: RoundRobinScheduler(time_quantum=2),
            RateMonotonicScheduler,
            DeadlineFirstScheduler
        ]
        wait_times = []
        turn_times = []
        for ctor in ctors:
            sched = ctor()
            for p in self.processes:
                sched.add_process(Process(
                    pid          = p.pid,
                    arrival_time = p.arrival_time,
                    burst_time   = p.burst_time,
                    period       = getattr(p, "period", None),
                    deadline     = getattr(p, "deadline", None)
                ))
            sched.schedule()
            wait_times.append(sched.average_waiting_time())
            turn_times.append(sched.average_turnaround_time())

        # full vs zoomed scale
        full_max = max(max(wait_times), max(turn_times), 1)
        zoom_max = max(
            turn_times[ labels.index("FCFS") ],
            turn_times[ labels.index("SJN") ],
            turn_times[ labels.index("RR") ],
            1
        )

        # ─── Draw bar chart ────────────────────────────────────────────────────────
        chart_x      = 50
        chart_y      = table_y + table_h + 50
        chart_w      = self.width - 100
        chart_h      = 200

        bc = BarChart(
            labels      = labels,
            wait_times  = wait_times,
            turn_times  = turn_times,
            x           = chart_x,
            y           = chart_y,
            width       = chart_w,
            height      = chart_h,
            bar_colors  = ((254,90,90),(90,180,254)),
            marker_count= 5,
           zoomed      = self.comparison_zoomed
        )
        bc.draw(self.screen, self.font)

        # ─── Back button ───────────────────────────────────────────────────────────
        btn_y = self.back_button["rect"].y
        self.back_button["rect"].topleft = (50, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        bl = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(bl, bl.get_rect(center=self.back_button["rect"].center))



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
        # Title
        title = self.font.load().render("Custom Process Input", True, (0,0,0))
        self.screen.blit(title, (50,50))

        # ─── Compute next‐arrival placeholder ─────────────────────────────────────────
        used = {int(p[0]) for p in self.custom_inputs}
        next_arr = 0
        while next_arr in used:
            next_arr += 1

        # placeholders
        arrival_ph  = str(next_arr)
        burst_ph    = "random"
        period_ph   = "random"
        deadline_ph = "random"

        # ─── Arrival box ──────────────────────────────────────────────────────────────
        lbl = self.font.load().render("Arrival:", True, (0,0,0))
        self.screen.blit(lbl, (50,120))
        self.arrival_box.draw(self.screen, placeholder=arrival_ph)

        # ─── Burst box ───────────────────────────────────────────────────────────────
        lbl = self.font.load().render("Burst:", True, (0,0,0))
        self.screen.blit(lbl, (200,120))
        self.burst_box.draw(self.screen, placeholder=burst_ph)

        # ─── Period box (RM & DF) ─────────────────────────────────────────────────────
        if self.selected_algo in ("RM", "DF"):
            lbl = self.font.load().render("Period:", True, (0,0,0))
            self.screen.blit(lbl, (350,120))
            self.period_box.draw(self.screen, placeholder=period_ph)

        # ─── Deadline box (DF only) ───────────────────────────────────────────────────
        if self.selected_algo == "DF":
            lbl = self.font.load().render("Deadline:", True, (0,0,0))
            self.screen.blit(lbl, (500,120))
            # reposition the input box to sit under the label
            self.deadline_box.rect.topleft = (500, self.deadline_box.rect.y)
            self.deadline_box.draw(self.screen, placeholder=deadline_ph)

        # ─── Add Process button ──────────────────────────────────────────────────────
        pygame.draw.rect(self.screen, (50,150,50), self.add_button["rect"])
        add_txt = self.font.load().render(self.add_button["label"], True, (255,255,255))
        self.screen.blit(add_txt, self.add_button["rect"].move(5,5))

        # ─── Table of Added Processes ────────────────────────────────────────────────
        from algorithms.process import Process
        table_x, table_y = 50, 220
        cols = ["#", "Arrival", "Burst"]
        if self.selected_algo in ("RM", "DF"):
            cols.append("Period")
        if self.selected_algo == "DF":
            cols.append("Deadline")

        rows = []
        for idx, (a,b,pr,dl) in enumerate(self.custom_inputs):
            rows.append(Process(
                pid=a,                
                arrival_time=a,
                burst_time=b,
                period=pr if self.selected_algo in ("RM","DF") else None,
                deadline=dl if self.selected_algo=="DF" else None
            ))

        self.table.draw(
            screen    = self.screen,
            x         = table_x,
            y         = table_y,
            cols      = cols,
            processes = rows,
            spacing   = 30,
            truncate  = 5
        )

        # ─── Bottom Buttons ──────────────────────────────────────────────────────────
        btn_y = self.height - 50 - self.back_button["rect"].height

        # Back (left)
        self.back_button["rect"].topleft = (50, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_txt = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(back_txt, back_txt.get_rect(center=self.back_button["rect"].center))

        # Start Simulation (right)
        w,h = self.start_sim_button["rect"].size
        sx  = self.width - 50 - w
        self.start_sim_button["rect"].topleft = (sx, btn_y)
        pygame.draw.rect(self.screen, (0,0,0), self.start_sim_button["rect"])
        start_txt = self.font.load().render(self.start_sim_button["label"], True, (255,255,255))
        self.screen.blit(start_txt, start_txt.get_rect(center=self.start_sim_button["rect"].center))



    def draw_results(self, processes, chart_top, chart_height, spacing_y=20, show_metrics=True):
        # Determine columns based on selected algorithm
        if self.selected_algo == "RM":
            cols = ["PID", "Arrival", "Burst", "Period"]
        elif self.selected_algo == "DF":
            cols = ["PID", "Arrival", "Burst", "Period", "Deadline"]
        else:
            cols = ["PID", "Arrival", "Burst"]

        # 1) Table (truncate to 5 rows)
        table_y = chart_top + chart_height + 50
        self.table.draw(
            screen    = self.screen,
            x         = self.margin_x,
            y         = table_y,
            cols      = cols,
            processes = processes,
            spacing   = 30,
            truncate  = 5
        )

        # 2) Metrics below the table
        cur_y = table_y + self.table.get_height() + spacing_y
        if show_metrics:
            ctr = Container(self.font, direction="col", spacing=5)
            ctr.add_text(f"Avg waiting time: {self.scheduler.average_waiting_time():.2f}")
            ctr.add_text(f"Avg turnaround time: {self.scheduler.average_turnaround_time():.2f}")
            ctr.draw(self.screen, self.margin_x, cur_y)

    
    def draw_simulation(self):
        display = self.selected_algo_display or ""
        title_surf = self.font.load(size="md", type="Black") \
                        .render(f"Simulation Result{f' – {display}' if display else ''}", True, (0,0,0))
        self.screen.blit(title_surf, (50,10))
        if not self.scheduler or not self.scheduler.timeline:
            return

        # ─── Gantt Chart ───────────────────────────────────────────────────────────────
        start_time = min(seg[1] for seg in self.scheduler.timeline)
        end_time   = max(seg[2] for seg in self.scheduler.timeline)
        total_time = max(end_time - start_time, 1)
        chart_top    = 150
        chart_height = 100
        chart_width  = self.width - 100

        # inside draw_simulation():
        gc = GanttChart(
            x=self.margin_x,
            y=chart_top,
            width=chart_width,
            height=chart_height,
            timeline=self.scheduler.timeline,
            process_colors=self.process_colors
        )
        gc.draw(self.screen, self.font)
        
        # Draw processes table and metrics
        self.draw_results(processes=self.processes, chart_height=chart_height, chart_top=chart_top)

        # ─── Buttons ───────────────────────────────────────────────────────────────────
        left_margin, right_margin = 50, 50
        btn_y = self.back_button["rect"].y

        # Back at left margin
        self.back_button["rect"].topleft = (left_margin, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        bl = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(bl, bl.get_rect(center=self.back_button["rect"].center))

        # Compare & Replay right-aligned
        spacing = 10
        right_btns = [(self.compare_button, (200,100,50)),
                    (self.replay_button,  (50,50,200))]
        total_w = sum(b["rect"].width for b,_ in right_btns) + spacing * (len(right_btns)-1)
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

        # ─── Static UI ────────────────────────────────────────────────────────────────
        title = self.font.load().render("Simulation Result (Replay)", True, (0,0,0))
        self.screen.blit(title, (50,10))

        # Compute chart geometry
        start_time   = min(seg[1] for seg in self.scheduler.timeline)
        end_time     = max(seg[2] for seg in self.scheduler.timeline)
        total_time   = end_time - start_time if end_time != start_time else 1
        chart_top    = 150
        chart_height = 100
        chart_left   = 50
        chart_width  = self.width - 100

        # X‐axis
        pygame.draw.line(
            self.screen, (0,0,0),
            (chart_left, chart_top+chart_height),
            (chart_left+chart_width, chart_top+chart_height),
            2
        )

        # Time markers
        for i in range(7):
            t  = start_time + i * (total_time/6)
            xm = chart_left + ((t - start_time) / total_time) * chart_width
            mark = self.font.load().render(f"{t:.1f}", True, (0,0,0))
            self.screen.blit(mark, (xm-10, chart_top+chart_height+5))

        # ─── Process Table (both random & custom) ─────────────────────────────────────
        self.draw_results(
            processes    = self.processes,
            chart_top    = chart_top,
            chart_height = chart_height,
        )

        # ─── Static Buttons ───────────────────────────────────────────────────────────
        left_margin, right_margin = 50, 50
        btn_y = self.back_button["rect"].y

        # Back at left
        self.back_button["rect"].topleft = (left_margin, btn_y)
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_lbl = self.font.load().render(self.back_button["label"], True, (255,255,255))
        self.screen.blit(back_lbl, back_lbl.get_rect(center=self.back_button["rect"].center))

        # Compare & Replay right-aligned
        spacing = 10
        right_btns = [
            (self.compare_button, (200,100,50)),
            (self.replay_button,  (50,50,200)),
        ]
        total_w = sum(b["rect"].width for b,_ in right_btns) + spacing * (len(right_btns)-1)
        x = self.width - right_margin - total_w
        for btn, color in right_btns:
            btn["rect"].topleft = (x, btn_y)
            pygame.draw.rect(self.screen, color, btn["rect"])
            lbl = self.font.load().render(btn["label"], True, (255,255,255))
            self.screen.blit(lbl, lbl.get_rect(center=btn["rect"].center))
            x += btn["rect"].width + spacing

        # ─── Animated Bars ────────────────────────────────────────────────────────────
        now      = pygame.time.get_ticks()
        elapsed  = now - self.replay_start_time
        progress = min(elapsed / self.replay_duration, 1.0)

        for pid, seg_start, seg_end in self.scheduler.timeline:
            norm_start = (seg_start - start_time) / total_time
            norm_end   = (seg_end   - start_time) / total_time

            if progress >= norm_start:
                portion = min(
                    1.0,
                    (progress - norm_start) /
                    ((norm_end - norm_start) if norm_end > norm_start else 1)
                )
                x0     = chart_left + norm_start * chart_width
                full_w = (norm_end - norm_start) * chart_width
                cur_w  = full_w * portion

                rect = pygame.Rect(x0, chart_top, cur_w, chart_height)
                color = self.process_colors.get(pid, (100,180,100))
                pygame.draw.rect(self.screen, color, rect)

                if progress >= norm_end:
                    pygame.draw.line(
                        self.screen, (0,0,0),
                        (x0+full_w, chart_top),
                        (x0+full_w, chart_top+chart_height),
                        2
                    )

                label = self.font.load().render(f"P{pid}", True, (255,255,255))
                self.screen.blit(label, rect.move(5,5))
 
    # ─── hyperperiod warning ─────────────────────────────────────────────────
    def handle_hyper_warning_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Auto fix → regenerate random with same count
            if self.hyper_auto_btn["rect"].collidepoint(pos):
                self.processes = generate_random_processes(
                    self.n_custom,
                    include_period=True,
                    include_deadline=True
                )
                self.initialize_scheduler()
                self.scheduler.schedule()
                self.state = "simulation"
                return
            # Manual → go back to custom input
            if self.hyper_manual_btn["rect"].collidepoint(pos):
                self.state = "input"
                return

    def draw_hyper_warning(self):
        # dim background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))

        # dialog
        w, h = 500, 200
        x, y = (self.width-w)//2, (self.height-h)//2
        pygame.draw.rect(self.screen, (245,245,245), (x,y,w,h), border_radius=8)
        pygame.draw.rect(self.screen, (0,0,0), (x,y,w,h), 2, border_radius=8)

        # message
        msg1 = f"Hyperperiod = {self.bad_hyper} exceeds {self.max_hyperperiod}"
        msg2 = "Gantt chart for RM/EDF will not render correctly."
        txt1 = self.font.load().render(msg1, True, (0,0,0))
        txt2 = self.font.load().render(msg2, True, (0,0,0))
        self.screen.blit(txt1, (x+20, y+40))
        self.screen.blit(txt2, (x+20, y+80))

        for btn in (self.hyper_manual_btn, self.hyper_auto_btn):
            pygame.draw.rect(self.screen, (0,0,0), btn["rect"])
            label = self.font.load().render(btn["label"], True, (255,255,255))
            self.screen.blit(label, label.get_rect(center=btn["rect"].center))

    def initialize_scheduler(self):
        # Set up the scheduler instance
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

        # Add all processes
        if self.scheduler:
            for p in self.processes:
                self.scheduler.add_process(p)

        # Assign each PID a stable random color if not already present
        for p in self.processes:
            if p.pid not in self.process_colors:
                self.process_colors[p.pid] = (
                    random.randint(50, 200),
                    random.randint(50, 200),
                    random.randint(50, 200)
                )


def main_pygame():
    app = SchedulerApp()
    app.run()

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    main_pygame()