import random
from algorithms.process import Process
# ---------------------------
# Utility Functions
# ---------------------------
def generate_random_processes(num_processes, arrival_range=(0, 10), burst_range=(1, 10), include_deadline=False):
    """
    Generate a list of processes with random arrival and burst times.
    If include_deadline is True, a deadline is generated for each process.
    Deadlines are set as: arrival_time + burst_time + random offset (0 to 5).
    """
    processes = []
    for i in range(num_processes):
        arrival_time = random.randint(*arrival_range)
        burst_time = random.randint(*burst_range)
        deadline = None
        if include_deadline:
            deadline = arrival_time + burst_time + random.randint(0, 5)
        processes.append(Process(pid=i+1, arrival_time=arrival_time, burst_time=burst_time, deadline=deadline))
    return processes

def display_process_info(processes):
    """Print detailed information for each process."""
    for p in processes:
        print(p)
