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

    def draw(self, screen, placeholder=''):
        # decide what to render: real text or placeholder
        if self.text:
            disp = self.text
            col  = self.color
        else:
            disp = placeholder
            col  = pygame.Color('grey')   # light grey for placeholder

        # re-render surface with chosen color
        self.txt_surface = pygame.font.Font(None, 24).render(disp, True, col)
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
        self.period_box   = TextInputBox(350, 150, 100, 32)
        # For replay animation.
        self.replaying = False
        self.replay_start_time = None
        self.replay_duration = 5000  # 5 seconds

        self.table = Table(self.width, self.height, self.font)
        self.margin_x = 50

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
        self.add_button = {"label": "Add Process", "rect": pygame.Rect(650, 150, 150, 32)}
        self.start_sim_button = {"label": "Start Simulation", "rect": pygame.Rect(500, 200, 200, 40)}
        # In simulation state.
        self.replay_button = {"label": "Replay", "rect": pygame.Rect(50, 600, 120, 40)}
        self.compare_button = {"label": "Compare Metrics", "rect": pygame.Rect(200, 550, 200, 40)}
        self.back_button = {"label": "Back to Menu", "rect": pygame.Rect(200, 600, 150, 40)}

        self.process_colors = {}

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
        # Let the table detect any "See all table" clicks first
        self.table.handle_event(
            event,
            cols=["PID", "Arrival", "Burst", "Deadline"],
            processes=self.processes,
            spacing=30
        )

        # Now handle the Back button
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
                        include_period   = self.selected_algo in ("RM","DF")
                        include_deadline = self.selected_algo == "DF"
                        self.processes = generate_random_processes(
                           5,
                            include_period=include_period,
                            include_deadline=include_deadline
                        )
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
        # First, let the table detect any "See all table" clicks
        from algorithms.process import Process
        proc_objs = [
            Process(pid=idx+1,
                    arrival_time=arrival,
                    burst_time=burst,
                    deadline=deadline,
                    period=deadline if self.selected_algo in ("RM", "DF") else None)
            for idx, (arrival, burst, deadline) in enumerate(self.custom_inputs)
        ]
        self.table.handle_event(
            event,
            cols=["#", "Arrival", "Burst", "Deadline"],
            processes=proc_objs,
            spacing=30
        )

        # Forward events to the input boxes
        self.arrival_box.handle_event(event)
        self.burst_box.handle_event(event)
        if self.selected_algo in ("RM", "DF"):
            self.deadline_box.handle_event(event)

        # Handle clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Add Process
            if self.add_button["rect"].collidepoint(pos):
                try:
                    # Compute next unused arrival
                    used = {int(p[0]) for p in self.custom_inputs}
                    next_arrival = 0
                    while next_arrival in used:
                        next_arrival += 1

                    # Arrival
                    if not self.arrival_box.text.strip():
                        arrival = next_arrival
                    else:
                        arrival = float(self.arrival_box.text)

                    # Burst
                    if not self.burst_box.text.strip():
                        burst = random.randint(1, 10)
                    else:
                        burst = float(self.burst_box.text)

                    # Deadline/Period
                    deadline = None
                    if self.selected_algo in ("RM", "DF"):
                        if not self.deadline_box.text.strip():
                            deadline = arrival + burst + random.randint(0, 5)
                        else:
                            deadline = float(self.deadline_box.text)

                    # Append to custom inputs
                    self.custom_inputs.append((arrival, burst, deadline))

                    # Clear input boxes
                    for box in (self.arrival_box, self.burst_box, self.deadline_box):
                        box.text = ""
                        box.txt_surface = pygame.font.Font(None, 24).render("", True, box.color)

                except Exception:
                    print("Invalid input! Please enter valid numbers.")

            # Start Simulation
            elif self.start_sim_button["rect"].collidepoint(pos):
                self.processes = []
                pid = 1
                for arrival, burst, deadline in self.custom_inputs:
                    if self.selected_algo == "RM":
                        # RM uses 'deadline' field as the period, ignores deadline
                        p = Process(
                            pid=pid,
                            arrival_time=arrival,
                            burst_time=burst,
                            deadline=None,
                            period=deadline
                        )
                    elif self.selected_algo == "DF":
                        # EDF uses both period and deadline
                        p = Process(
                            pid=pid,
                            arrival_time=arrival,
                            burst_time=burst,
                            deadline=deadline,
                            period=deadline
                        )
                    else:
                        # Other algos ignore deadline/period
                        p = Process(
                            pid=pid,
                            arrival_time=arrival,
                            burst_time=burst
                        )
                    self.processes.append(p)
                    pid += 1

                if not self.processes:
                    print("No processes entered!")
                    return

                self.initialize_scheduler()
                self.scheduler.schedule()
                self.state = "simulation"

            # Back to Menu
            elif self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
                self.custom_inputs = []


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
        title_surf = self.font.load().render(
            "Comparison: Avg Waiting & Turnaround Times", True, (0,0,0)
        )
        self.screen.blit(title_surf, (50, 10))

        # ─── Process Table (with truncation) ───────────────────────────────────────────
        table_x = 50
        table_y = 50
        cols    = ["PID", "Arrival", "Burst", "Deadline"]
        truncate_count = 5
        # draw up to `truncate_count` rows, with "See all table" if more
        self.table.draw(
            screen    = self.screen,
            x         = table_x,
            y         = table_y,
            cols      = cols,
            processes = self.processes,
            spacing   = 30,
            truncate  = truncate_count
        )
        table_h = self.table.get_height()

        chart_x      = 50
        chart_y      = table_y + table_h + 80
        chart_w      = self.width - 100
        chart_h      = 200

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
                sched.add_process(Process(
                    pid          = orig.pid,
                    arrival_time = orig.arrival_time,
                    burst_time   = orig.burst_time,
                    deadline     = orig.deadline if self.selected_algo=="DF" else None,
                    period       = orig.deadline if self.selected_algo in ("RM","DF") else None
                ))
            sched.schedule()
            wait_times.append(sched.average_waiting_time())
            turn_times.append(sched.average_turnaround_time())

        bc = BarChart(
            labels=labels,
            wait_times  = wait_times,
            turn_times  = turn_times,
            x           = chart_x,
            y           = chart_y,
            width       = chart_w,
            height      = chart_h,
            bar_colors  = ((254,90,90),(90,180,254)),
            marker_count= 5   # or 0 if you don’t want grid/ticks
        )

        bc.draw(self.screen, self.font)

        # ─── Back button ───────────────────────────────────────────────────────────────
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
                pid=a,                # or idx+1 if you prefer
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


    def handle_input_event(self, event):
        # Let "See all table" clicks go to the table
        from algorithms.process import Process
        proc_objs = [
            Process(pid=idx+1,
                    arrival_time=a,
                    burst_time=b,
                    deadline=dl if self.selected_algo=="DF" else None,
                    period=pr if self.selected_algo in ("RM","DF") else None)
            for idx,(a,b,pr,dl) in enumerate(self.custom_inputs)
        ]
        self.table.handle_event(
            event,
            cols=["#","Arrival","Burst"] + (["Period"] if self.selected_algo in ("RM","DF") else []) + (["Deadline"] if self.selected_algo=="DF" else []),
            processes=proc_objs,
            spacing=30
        )

        # Boxes
        self.arrival_box.handle_event(event)
        self.burst_box.handle_event(event)
        if self.selected_algo in ("RM","DF"):
            self.period_box.handle_event(event)
        if self.selected_algo == "DF":
            self.deadline_box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Add
            if self.add_button["rect"].collidepoint(pos):
                try:
                    # arrival
                    arrival = float(self.arrival_box.text) if self.arrival_box.text.strip() else \
                              next(i for i in range(1000) if i not in {int(x[0]) for x in self.custom_inputs})
                    # burst
                    burst   = float(self.burst_box.text) if self.burst_box.text.strip() else random.randint(1,10)
                    # period
                    pr = None
                    if self.selected_algo in ("RM","DF"):
                        pr = float(self.period_box.text) if self.period_box.text.strip() else random.randint( burst+1, burst+10 )
                    # deadline
                    dl = None
                    if self.selected_algo == "DF":
                        dl = float(self.deadline_box.text) if self.deadline_box.text.strip() else arrival + burst + random.randint(0,5)

                    self.custom_inputs.append((arrival, burst, pr, dl))
                    for box in (self.arrival_box, self.burst_box, self.period_box, self.deadline_box):
                        box.text = ""
                        box.txt_surface = pygame.font.Font(None,24).render("",True,box.color)
                except Exception:
                    print("Invalid input!")

            # Start Simulation
            elif self.start_sim_button["rect"].collidepoint(pos):
                self.processes = []
                pid = 1
                for a,b,pr,dl in self.custom_inputs:
                    self.processes.append(Process(
                        pid=pid,
                        arrival_time=a,
                        burst_time=b,
                        deadline=dl if self.selected_algo=="DF" else None,
                        period=pr if self.selected_algo in ("RM","DF") else None
                    ))
                    pid += 1
                if not self.processes:
                    print("No processes entered!")
                    return
                self.initialize_scheduler()
                self.scheduler.schedule()
                self.state = "simulation"

            # Back
            elif self.back_button["rect"].collidepoint(pos):
                self.state = "menu"
                self.custom_inputs.clear()

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
        
        # Draw processes table and metrics...
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