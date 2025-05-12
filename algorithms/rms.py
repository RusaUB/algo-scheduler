from algorithms.scheduler import Scheduler

class RateMonotonicScheduler(Scheduler):
    """
    Rate Monotonic (RM) scheduling using non-preemptive fixed priority.
    For this example, the process deadline is treated as its period;
    processes with earlier deadlines (shorter periods) have higher priority.
    """
    def schedule(self):
        unscheduled = self.processes.copy()
        current_time = 0
        while unscheduled:
            ready_queue = [p for p in unscheduled if p.arrival_time <= current_time]
            if not ready_queue:
                current_time = min(unscheduled, key=lambda p: p.arrival_time).arrival_time
                ready_queue = [p for p in unscheduled if p.arrival_time <= current_time]
            process = min(ready_queue, key=lambda p: p.deadline)
            process.start_time = current_time
            process.completion_time = current_time + process.burst_time
            process.waiting_time = current_time - process.arrival_time
            process.turnaround_time = process.completion_time - process.arrival_time
            self.timeline.append((process.pid, process.start_time, process.completion_time))
            current_time += process.burst_time
            unscheduled.remove(process)
