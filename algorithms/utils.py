import random
from algorithms.process import Process
from math import gcd

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)

def hyperperiod(periods):
    h = 1
    for p in periods:
        h = lcm(h, p)
    return h

def generate_random_processes(
    num_processes: int,
    arrival_increment: bool = True,
    burst_range=(1, 10),
    include_period=False,
    include_deadline=False,
    max_hyperperiod=50
):
    """
    arrival_increment=True → arrivals = 0,1,2,...
    include_period    → generate periods burst+rand(1,10) *but* resample
                         until lcm(periods) <= max_hyperperiod
    include_deadline  → deadline = arrival + burst + rand(0,5)
    """
    # 1) arrivals = 0,1,2,...
    arrivals = list(range(num_processes))

    # 2) bursts
    bursts = [random.randint(*burst_range) for _ in range(num_processes)]

    # 3) periods (if requested), else all None
    periods = [None] * num_processes
    if include_period:
        # repeatedly sample until hyperperiod small enough
        while True:
            cand = [b + random.randint(1, 10) for b in bursts]
            if hyperperiod(cand) <= max_hyperperiod:
                periods = cand
                break

    # 4) deadlines
    deadlines = [
        (arr + b + random.randint(0, 5)) if include_deadline else None
        for arr, b in zip(arrivals, bursts)
    ]

    procs = []
    for pid, (a, b, pr, dl) in enumerate(zip(arrivals, bursts, periods, deadlines), start=1):
        procs.append(Process(
            pid=pid,
            arrival_time=a,
            burst_time=b,
            period=pr,
            deadline=dl
        ))
    return procs


def display_process_info(processes):
    """Print detailed information for each process."""
    for p in processes:
        print(p)
