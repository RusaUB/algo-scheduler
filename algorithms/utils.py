import random
from algorithms.process import Process

# ---------------------------
# Utility Functions
# ---------------------------
def generate_random_processes(
    num_processes,
    arrival_range=(0, 10),
    burst_range=(1, 10),
    include_period=False,
    include_deadline=False
):
    """
    Generate a list of processes with unique random arrival times.
    
    Parameters:
      num_processes   – number of processes to generate
      arrival_range   – tuple (min_arrival, max_arrival)
      burst_range     – tuple (min_burst, max_burst)
      include_period  – if True, assign each process a random period > burst_time
      include_deadline– if True, assign each process an absolute deadline
    
    Deadlines (if used) are set to arrival_time + burst_time + random offset [0,5].
    Periods (if used) are chosen as burst_time + random offset [1,10].
    """
    min_a, max_a = arrival_range
    span = max_a - min_a + 1
    if num_processes > span:
        raise ValueError(
            f"Cannot generate {num_processes} unique arrival times "
            f"in range {arrival_range}"
        )

    # pick unique arrival times
    arrival_times = random.sample(range(min_a, max_a + 1), num_processes)

    processes = []
    for i, arrival_time in enumerate(arrival_times, start=1):
        burst_time = random.randint(*burst_range)

        # optional period (for RM & EDF)
        period = None
        if include_period:
            period = burst_time + random.randint(1, 10)

        # optional deadline (for EDF)
        deadline = None
        if include_deadline:
            deadline = arrival_time + burst_time + random.randint(0, 5)

        processes.append(Process(
            pid=           i,
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
