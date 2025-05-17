from algorithms.scheduler import Scheduler

class RateMonotonicScheduler(Scheduler):
    """
    Rate Monotonic (RM): non‐preemptive fixed‐priority by period only.
    Requires that every Process has a non‐None `.period` and ignores any `.deadline`.
    """
    def schedule(self):
        # ── Enforce that every process has a period defined ────────────────────
        for p in self.processes:
            if p.period is None:
                raise ValueError(f"RM scheduling requires a period for Process {p.pid}")

        unscheduled  = list(self.processes)
        current_time = 0

        while unscheduled:
            # build ready queue
            ready = [p for p in unscheduled if p.arrival_time <= current_time]
            if not ready:
                # jump to the next arrival
                current_time = min(unscheduled, key=lambda p: p.arrival_time).arrival_time
                ready = [p for p in unscheduled if p.arrival_time <= current_time]

            # pick the task with the shortest period
            proc = min(ready, key=lambda p: p.period)

            # record its scheduling interval
            proc.start_time      = current_time
            proc.completion_time = current_time + proc.burst_time
            proc.waiting_time    = proc.start_time - proc.arrival_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time

            self.timeline.append((proc.pid, proc.start_time, proc.completion_time))

            # advance time and remove from unscheduled
            current_time += proc.burst_time
            unscheduled.remove(proc)
