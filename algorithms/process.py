class Process:
    """
    Represents a process to be scheduled.

    Parameters:
        pid: Unique process identifier.
        arrival_time: Time at which the process enters the system.
        burst_time: Total execution time needed by the process.
        deadline: (Optional) The deadline by which the process should be completed.
    """
    def __init__(self, pid, arrival_time, burst_time, deadline=None):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time  # For preemptive schedulers.
        self.deadline = deadline
        
        # Optional performance metrics; set during scheduling.
        self.start_time = None
        self.completion_time = None
        self.waiting_time = None
        self.turnaround_time = None

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival_time={self.arrival_time}, "
                f"burst_time={self.burst_time}, deadline={self.deadline})")
