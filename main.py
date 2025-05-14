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
                        self.selected_algo = btn["algo"]
                        self.custom_inputs = []
                        self.processes = []
                        self.state = "input"
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
        self.screen.fill((240,240,240))
        # Title
        title = self.font.load().render("Comparison: Processes & Avg Metrics", True, (0,0,0))
        self.screen.blit(title, (50,10))

        # 1) Show all processes
        proc_title = self.font.load().render("Processes:", True, (0,0,0))
        self.screen.blit(proc_title, (50,50))
        y = 80
        for p in self.processes:
            details = f"P{p.pid}: Arrival={p.arrival_time}, Burst={p.burst_time}"
            if p.deadline is not None:
                details += f", Deadline={p.deadline}"
            line = self.font.load().render(details, True, (0,0,0))
            self.screen.blit(line, (50, y))
            y += 25

        # Spacer
        y += 10
        metrics_title = self.font.load().render("Average Waiting / Turnaround Times:", True, (0,0,0))
        self.screen.blit(metrics_title, (50, y))
        y +=  30

        # 2) Compare algorithms
        labels = ["FCFS", "SJN", "RR", "RM", "DF"]
        algos  = [
            FCFS_Scheduler,
            ShortestJobNextScheduler,
            lambda: RoundRobinScheduler(time_quantum=2),
            RateMonotonicScheduler,
            DeadlineFirstScheduler
        ]

        for lbl, ctor in zip(labels, algos):
            sched = ctor()
            for orig in self.processes:
                arrival, burst, dead = orig.arrival_time, orig.burst_time, orig.deadline
                # supply default for RM/DF only if needed
                if lbl in ("RM", "DF") and dead is None:
                    dead = arrival + burst + 3
                proc_copy = Process(orig.pid, arrival, burst, dead)
                sched.add_process(proc_copy)

            sched.schedule()
            awt  = sched.average_waiting_time()
            atat = sched.average_turnaround_time()
            text = f"{lbl}: Avg wait = {awt:.2f}, Avg turn = {atat:.2f}"
            txt_surf = self.font.load().render(text, True, (0,0,0))
            self.screen.blit(txt_surf, (50, y))
            y += 25

        # Back button
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_text = self.font.load().render("Back", True, (255,255,255))
        self.screen.blit(back_text, self.back_button["rect"].move(10,5))


    def draw_menu(self):
        # 1) Main title at top‐left
        title_surf = self.font.load().render("Scheduling Simulator - Menu", True, (0, 0, 0))
        self.screen.blit(title_surf, (50, 10))

        # 2) Draw algorithm cards
        for card in self.algo_buttons:
            card.draw(self.screen)

        # 3) “Select Process Mode” + buttons in a horizontal row, bottom‐right
        label_surf = self.font.load().render("Select Process Mode:", True, (0, 0, 0))
        label_w, label_h = label_surf.get_size()

        # assume all mode buttons are same size
        btn_w, btn_h = self.mode_buttons[0]["rect"].size
        spacing     = 10
        margin      = 20

        total_btns_w = len(self.mode_buttons) * btn_w + (len(self.mode_buttons) - 1) * spacing
        total_w      = label_w + spacing + total_btns_w

        start_x = self.width - margin - total_w
        y       = self.height - margin - btn_h

        # draw the label
        self.screen.blit(label_surf, (start_x, y + (btn_h - label_h) // 2))

        # draw each button to the right of the label
        x = start_x + label_w + spacing
        for btn in self.mode_buttons:
            btn["rect"].topleft = (x, y)
            color = (0, 200, 0) if self.process_mode == btn["mode"] else (200, 200, 200)
            pygame.draw.rect(self.screen, color, btn["rect"])
            lbl_surf = self.font.load().render(btn["label"], True, (0, 0, 0))
            # center text inside the button
            lbl_x = x + (btn_w - lbl_surf.get_width()) // 2
            lbl_y = y + (btn_h - lbl_surf.get_height()) // 2
            self.screen.blit(lbl_surf, (lbl_x, lbl_y))
            x += btn_w + spacing

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
    
    def draw_simulation(self):
        title = self.font.load().render("Simulation Result", True, (0,0,0))
        self.screen.blit(title, (50,10))
        if not self.scheduler or not self.scheduler.timeline:
            return
        start_time = min(seg[1] for seg in self.scheduler.timeline)
        end_time = max(seg[2] for seg in self.scheduler.timeline)
        total_time = end_time - start_time if end_time != start_time else 1
        chart_top = 150
        chart_height = 100
        chart_left = 50
        chart_width = self.width - 100
        axis_color = (0,0,0)
        pygame.draw.line(self.screen, axis_color, (chart_left, chart_top+chart_height),
                         (chart_left+chart_width, chart_top+chart_height), 2)
        for seg in self.scheduler.timeline:
            pid, seg_start, seg_end = seg
            x = chart_left + ((seg_start - start_time) / total_time) * chart_width
            width = ((seg_end - seg_start) / total_time) * chart_width
            rect = pygame.Rect(x, chart_top, width, chart_height)
            pygame.draw.rect(self.screen, (100,180,100), rect)
            # Draw vertical divider.
            pygame.draw.line(self.screen, (0,0,0), (x+width, chart_top), (x+width, chart_top+chart_height), 2)
            label = self.font.load().render(f"P{pid}", True, (255,255,255))
            self.screen.blit(label, rect.move(5,5))
        num_markers = 6
        for i in range(num_markers+1):
            t = start_time + i * (total_time/num_markers)
            x = chart_left + ((t - start_time) / total_time) * chart_width
            time_label = self.font.load().render(f"{t:.1f}", True, (0,0,0))
            self.screen.blit(time_label, (x-10, chart_top+chart_height+5))
        pygame.draw.rect(self.screen, (50,50,200), self.replay_button["rect"])
        rep_text = self.font.load().render(self.replay_button["label"], True, (255,255,255))
        self.screen.blit(rep_text, self.replay_button["rect"].move(5,5))
        pygame.draw.rect(self.screen, (200,100,50), self.compare_button["rect"])
        cmp_text = self.font.load().render(self.compare_button["label"], True, (255,255,255))
        self.screen.blit(cmp_text, self.compare_button["rect"].move(5,5))
        pygame.draw.rect(self.screen, (100,100,100), self.back_button["rect"])
        back_text = self.font.load().render("Back", True, (255,255,255))
        self.screen.blit(back_text, self.back_button["rect"].move(10,5))
        # If in random mode, list the randomly produced processes with all parameters.
        if self.process_mode == "random":
            proc_title = self.font.load().render("Random Processes:", True, (0,0,0))
            self.screen.blit(proc_title, (50, chart_top+chart_height+50))
            y = chart_top+chart_height+80
            for p in self.processes:
                details = f"P{p.pid}: Arrival={p.arrival_time}, Burst={p.burst_time}"
                if p.deadline is not None:
                    details += f", Deadline={p.deadline}"
                proc_line = self.font.load().render(details, True, (0,0,0))
                self.screen.blit(proc_line, (50, y))
                y += 30

        # ==== INSERT AVERAGE METRICS HERE ====
        avg_wt = self.scheduler.average_waiting_time()
        avg_tat = self.scheduler.average_turnaround_time()
        wt_text = self.font.load().render(f"Avg waiting time: {avg_wt:.2f}", True, (0,0,0))
        tat_text = self.font.load().render(f"Avg turnaround time: {avg_tat:.2f}", True, (0,0,0))
        # position them below the process list
        self.screen.blit(wt_text, (chart_left, chart_top + chart_height + 250))
        self.screen.blit(tat_text, (chart_left, chart_top + chart_height + 280))
    
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
            for p in self.processes:
                details = f"P{p.pid}: Arrival={p.arrival_time}, Burst={p.burst_time}"
                if p.deadline is not None:
                    details += f", Deadline={p.deadline}"
                proc_line = self.font.load().render(details, True, (0,0,0))
                self.screen.blit(proc_line, (50, y))
                y += 30

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