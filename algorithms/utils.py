import random
from algorithms.process import Process
# ---------------------------
# Utility Functions
# ---------------------------
def generate_random_processes(num_processes, arrival_range=(0, 10), burst_range=(1, 10), include_deadline=False):
    """
    Generate a list of processes with unique random arrival and burst times.
    If include_deadline is True, a deadline is generated for each process
    as arrival_time + burst_time + random offset (0 to 5).
    """
    min_a, max_a = arrival_range
    span = max_a - min_a + 1
    if num_processes > span:
        raise ValueError(f"Cannot generate {num_processes} unique arrivals "
                         f"within range {arrival_range}")

    # pick unique arrival times
    arrival_times = random.sample(range(min_a, max_a + 1), num_processes)

    processes = []
    for i, arrival_time in enumerate(arrival_times):
        burst_time = random.randint(*burst_range)
        deadline = None
        if include_deadline:
            deadline = arrival_time + burst_time + random.randint(0, 5)
        processes.append(Process(
            pid=i+1,
            arrival_time=arrival_time,
            burst_time=burst_time,
            deadline=deadline
        ))
    return processes

def display_process_info(processes):
    """Print detailed information for each process."""
    for p in processes:
        print(p)
