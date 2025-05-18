from algorithms.scheduler import Scheduler

class ShortestJobNextScheduler(Scheduler):
    """
    Non-preemptive Shortest Job Next (SJN) scheduling.
    Inserts an “idle” segment (with empty PID) whenever there's
    a gap between the current time and the next process arrival.
    """
    def schedule(self):
        unscheduled  = self.processes.copy()
        current_time = 0

        while unscheduled:
            # build the ready queue
            ready_queue = [p for p in unscheduled if p.arrival_time <= current_time]

            if not ready_queue:
                # no one is ready → idle until the next arrival
                next_arrival = min(unscheduled, key=lambda p: p.arrival_time).arrival_time
                # record an unlabeled idle span
                self.timeline.append(("", current_time, next_arrival))
                current_time = next_arrival
                ready_queue = [p for p in unscheduled if p.arrival_time <= current_time]

            # pick the shortest-burst process
            proc = min(ready_queue, key=lambda p: p.burst_time)

            # schedule it
            start = current_time
            end   = start + proc.burst_time

            proc.start_time      = start
            proc.completion_time = end
            proc.waiting_time    = start - proc.arrival_time
            proc.turnaround_time = end   - proc.arrival_time

            self.timeline.append((proc.pid, start, end))

            # advance and remove
            current_time += proc.burst_time
            unscheduled.remove(proc)
