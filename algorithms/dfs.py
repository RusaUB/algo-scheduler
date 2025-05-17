from math import gcd
from functools import reduce
from copy import deepcopy
from algorithms.scheduler import Scheduler

class DeadlineFirstScheduler(Scheduler):
    """
    Preemptive Earliest-Deadline-First over the hyperperiod.
    Each Process must have:
      - .period    (int)
      - .burst_time (capacity)
      - .deadline  (relative, int)
    """

    def schedule(self):
        if not self.processes:
            return

        # 1) Validate
        for p in self.processes:
            if p.period is None or p.deadline is None:
                raise ValueError(f"EDF requires both period and deadline for P{p.pid}")

        # 2) Compute hyperperiod = lcm of all periods
        periods = [int(p.period) for p in self.processes]
        hyper = reduce(lambda a, b: a * b // gcd(a, b), periods)

        # 3) Initialize runtime state
        RT = {}
        for p in self.processes:
            RT[p.pid] = {
                'orig_period'   : int(p.period),
                'orig_capacity' : int(p.burst_time),
                'orig_deadline' : int(p.deadline),
                'current_capacity': int(p.burst_time),
                # first absolute deadline at t=0 is deadline itself
                'current_deadline': int(p.deadline)
            }

        timeline = []  # will build list of {'task': pid, 'start':, 'end':}

        # 4) Tick-by-tick simulation
        for t in range(hyper):
            # a) choose all with current_capacity>0
            ready = [pid for pid,info in RT.items() if info['current_capacity'] > 0]
            if ready:
                # pick the one with smallest current_deadline
                pid = min(ready, key=lambda i: RT[i]['current_deadline'])
                info = RT[pid]
                # consume one unit
                info['current_capacity'] -= 1

                # append or extend last segment
                if timeline and timeline[-1]['task'] == pid and timeline[-1]['end'] == t:
                    timeline[-1]['end']   = t+1
                    timeline[-1]['length'] += 1
                else:
                    timeline.append({
                        'task': pid,
                        'start': t,
                        'end':   t+1,
                        'length': 1
                    })
            # else: idle (we skip)

            # b) at end of tick, reload any whose (t+1)%period==0
            for pid, info in RT.items():
                if (t+1) % info['orig_period'] == 0:
                    info['current_capacity'] = info['orig_capacity']
                    info['current_deadline'] = (t+1) + info['orig_deadline']

        # 5) Flatten our dict‐style timeline into self.timeline = [(pid,start,end),...]
        self.timeline = [(seg['task'], seg['start'], seg['end']) for seg in timeline]

        # 6) Compute metrics
        for p in self.processes:
            segs = [s for s in self.timeline if s[0] == p.pid]
            if segs:
                last_finish = segs[-1][2]
                p.completion_time = last_finish
                p.turnaround_time = last_finish - p.arrival_time
                p.waiting_time    = p.turnaround_time - p.burst_time
