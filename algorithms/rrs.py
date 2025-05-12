from algorithms.scheduler import Scheduler

class RoundRobinScheduler(Scheduler):
    """Round Robin scheduling."""
    def __init__(self, time_quantum):
        super().__init__()
        self.time_quantum = time_quantum

    def schedule(self):
        if not self.processes:
            return
        self.processes.sort(key=lambda p: p.arrival_time)
        current_time = self.processes[0].arrival_time
        ready_queue = []
        index = 0
        while ready_queue or index < len(self.processes):
            while index < len(self.processes) and self.processes[index].arrival_time <= current_time:
                ready_queue.append(self.processes[index])
                index += 1
            if not ready_queue:
                current_time = self.processes[index].arrival_time
                continue
            process = ready_queue.pop(0)
            exec_time = min(self.time_quantum, process.remaining_time)
            start_time = current_time
            current_time += exec_time
            end_time = current_time
            self.timeline.append((process.pid, start_time, end_time))
            process.remaining_time -= exec_time
            while index < len(self.processes) and self.processes[index].arrival_time <= current_time:
                ready_queue.append(self.processes[index])
                index += 1
            if process.remaining_time > 0:
                ready_queue.append(process)

        for p in self.processes:
            # collect all segments for this process
            segments = [seg for seg in self.timeline if seg[0] == p.pid]
            if not segments:
                continue
            # the end of the last segment is the completion time
            p.completion_time = segments[-1][2]
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time    = p.turnaround_time - p.burst_time