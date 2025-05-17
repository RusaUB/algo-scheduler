from math import gcd
from copy import deepcopy
from algorithms.scheduler import Scheduler

class RateMonotonicScheduler(Scheduler):
    """
    Preemptive, periodic RM over the LCM(hyperperiod) of all task periods.
    """

    def schedule(self):
        if not self.processes:
            return

        # 1) Make sure every Process has a period
        for p in self.processes:
            if p.period is None:
                raise ValueError(f"RM requires a period for Process {p.pid}")

        # 2) Compute hyperperiod = lcm of all periods
        periods = [int(p.period) for p in self.processes]
        hyper = periods[0]
        for P in periods[1:]:
            hyper = hyper * P // gcd(hyper, P)

        # 3) Prepare a dynamic copy of each task
        RT = {}  # pid → { period, remaining, orig_period, orig_wc }
        for p in self.processes:
            RT[p.pid] = {
                'period'      : int(p.period),
                'remaining'   : int(p.burst_time),
                'orig_period' : int(p.period),
                'orig_wc'     : int(p.burst_time)
            }

        # 4) Simulate tick-by-tick
        for t in range(hyper):
            # collect ready tasks
            ready = [pid for pid,info in RT.items() if info['remaining'] > 0]
            if ready:
                # pick the one with smallest current period
                pid = min(ready, key=lambda i: RT[i]['period'])
                # record this 1‐unit slice
                self.timeline.append((pid, t, t+1))
                # consume one unit
                RT[pid]['remaining'] -= 1
            # else: CPU idle for this tick (we simply skip)

            # decrement everyone’s period counter
            for info in RT.values():
                info['period'] -= 1

            # any task whose period expired? reload it
            for pid, info in RT.items():
                if info['period'] == 0:
                    info['period']    = info['orig_period']
                    info['remaining'] = info['orig_wc']

        # 5) Merge adjacent segments
        self._merge_timeline_segments()

        # 6) Compute final metrics: we treat the last completion of each
        # instance as the “completion_time” for that PID
        for p in self.processes:
            segs = [seg for seg in self.timeline if seg[0] == p.pid]
            if segs:
                last_end = segs[-1][2]
                p.completion_time  = last_end
                p.turnaround_time  = last_end - p.arrival_time
                p.waiting_time     = p.turnaround_time - p.burst_time

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
