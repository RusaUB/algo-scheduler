
from algorithms.scheduler import Scheduler

class DeadlineFirstScheduler(Scheduler):
    """
    Deadline First (DF) scheduling using preemptive Earliest Deadline First (EDF).
    At each time unit, the process with the earliest deadline among those available is selected.
    """
    def schedule(self):
        if not self.processes:
            return
        current_time = min(p.arrival_time for p in self.processes)
        ready_queue = []
        unfinished = {p.pid: p for p in self.processes}
        current_process = None
        segment_start = current_time

        while unfinished:
            for p in self.processes:
                if p.arrival_time <= current_time and p not in ready_queue and p.pid in unfinished:
                    ready_queue.append(p)
            if not ready_queue:
                next_arrival = min((p.arrival_time for p in self.processes if p.pid in unfinished), default=current_time)
                if current_process is not None:
                    self.timeline.append((current_process.pid, segment_start, next_arrival))
                    current_process = None
                current_time = next_arrival
                segment_start = current_time
                continue

            candidate = min(ready_queue, key=lambda p: p.deadline)
            if current_process is None or candidate.pid != current_process.pid:
                if current_process is not None:
                    self.timeline.append((current_process.pid, segment_start, current_time))
                current_process = candidate
                segment_start = current_time

            current_process.remaining_time -= 1
            current_time += 1
            if current_process.remaining_time == 0:
                self.timeline.append((current_process.pid, segment_start, current_time))
                ready_queue.remove(current_process)
                del unfinished[current_process.pid]
                current_process = None
                segment_start = current_time

        self._merge_timeline_segments()
        for p in self.processes:
            segments = [seg for seg in self.timeline if seg[0] == p.pid]
            if segments:
                p.completion_time = segments[-1][2]
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.burst_time

    def _merge_timeline_segments(self):
        merged = []
        if not self.timeline:
            return
        current = self.timeline[0]
        for seg in self.timeline[1:]:
            if seg[0] == current[0] and seg[1] == current[2]:
                current = (current[0], current[1], seg[2])
            else:
                merged.append(current)
                current = seg
        merged.append(current)
        self.timeline = merged
