import random
from algorithms.process import Process

def generate_random_processes(
    num_processes,
    burst_range=(1, 5),
    include_period=False,
    include_deadline=False
):
    """
    Generate a list of processes with strictly sequential arrival times starting at 0.

    Arrival times: 0, 1, 2, ..., num_processes-1.
    Burst times: random in burst_range.
    Periods (if used): burst_time + random offset [1,10].
    Deadlines (if used): unique integers between arrival+burst and 10.
    """
    processes = []
    seen_deadlines = set()

    for i in range(num_processes):
        arrival_time = i
        burst_time   = random.randint(*burst_range)

        # optional period
        period = None
        if include_period:
            period = burst_time + random.randint(1, 10)

        # optional unique deadline capped at 10
        deadline = None
        if include_deadline:
            # earliest possible deadline
            earliest = arrival_time + burst_time
            if earliest > 10:
                earliest = 10

            # build candidate pool [earliest..10] minus already used
            pool = [d for d in range(earliest, 11) if d not in seen_deadlines]
            if not pool:
                # if exhausted, just pick ‘10’ (we can no longer guarantee uniqueness)
                cand = 10
            else:
                cand = random.choice(pool)

            deadline = cand
            seen_deadlines.add(deadline)

        processes.append(Process(
            pid=           i+1,
            arrival_time=  arrival_time,
            burst_time=    burst_time,
            deadline=      deadline,
            period=        period
        ))

    return processes




def display_process_info(processes):
    """Print detailed information for each process."""
    for p in processes:
        print(p)
