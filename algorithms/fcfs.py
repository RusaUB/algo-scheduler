from algorithms.scheduler import Scheduler

class FCFS_Scheduler(Scheduler):
    """First-Come-First-Served scheduling."""
    def schedule(self):
        self.processes.sort(key=lambda p: p.arrival_time)
        current_time = 0
        for process in self.processes:
            start_time = max(current_time, process.arrival_time)
            finish_time = start_time + process.burst_time
            self.timeline.append((process.pid, start_time, finish_time))
            process.start_time = start_time
            process.completion_time = finish_time
            process.waiting_time = start_time - process.arrival_time
            process.turnaround_time = finish_time - process.arrival_time
            current_time = finish_time
