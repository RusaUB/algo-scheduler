from algorithms.scheduler import Scheduler

class DeadlineFirstScheduler(Scheduler):
    """
    Earliest Deadline First (EDF): preemptive, picks the ready process
    with the earliest absolute deadline. Now *requires* that every
    Process has a non-None `.period` field.
    """
    def schedule(self):
        # ── Enforce that every process has a period defined ────────────────────
        for p in self.processes:
            if p.period is None:
                raise ValueError(f"EDF scheduling requires a period for Process {p.pid}")

        if not self.processes:
            return

        current_time  = min(p.arrival_time for p in self.processes)
        ready_queue   = []
        unfinished    = {p.pid: p for p in self.processes}
        current_proc  = None
        segment_start = current_time

        while unfinished:
            # enqueue newly arrived tasks
            for p in self.processes:
                if (p.arrival_time <= current_time
                    and p.pid in unfinished
                    and p not in ready_queue):
                    ready_queue.append(p)

            if not ready_queue:
                # idle until next arrival
                next_arr = min(
                    (p.arrival_time for p in self.processes if p.pid in unfinished),
                    default=current_time
                )
                if current_proc:
                    self.timeline.append((current_proc.pid, segment_start, next_arr))
                    current_proc = None
                current_time  = next_arr
                segment_start = next_arr
                continue

            # pick by earliest deadline
            proc = min(ready_queue,
                       key=lambda p: p.deadline if p.deadline is not None else float('inf'))

            # on context-switch, close old segment
            if current_proc is None or proc.pid != current_proc.pid:
                if current_proc:
                    self.timeline.append((current_proc.pid, segment_start, current_time))
                current_proc  = proc
                segment_start = current_time

            # execute one time unit
            current_proc.remaining_time -= 1
            current_time += 1

            # if it finishes, close its segment
            if current_proc.remaining_time == 0:
                self.timeline.append((current_proc.pid, segment_start, current_time))
                ready_queue.remove(current_proc)
                del unfinished[current_proc.pid]
                current_proc  = None
                segment_start = current_time

        # coalesce contiguous segments
        self._merge_timeline_segments()

        # record final metrics
        for p in self.processes:
            segs = [s for s in self.timeline if s[0] == p.pid]
            if segs:
                p.completion_time = segs[-1][2]
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time    = p.turnaround_time - p.burst_time

    def _merge_timeline_segments(self):
        merged = []
        if not self.timeline:
            return
        curr = self.timeline[0]
        for seg in self.timeline[1:]:
            if seg[0] == curr[0] and seg[1] == curr[2]:
                curr = (curr[0], curr[1], seg[2])
            else:
                merged.append(curr)
                curr = seg
        merged.append(curr)
        self.timeline = merged
