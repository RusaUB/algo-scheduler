class Process:
    """
    Represents a process/task.

    Parameters:
        pid: Unique ID.
        arrival_time: when it becomes ready.
        burst_time: CPU time required.
        deadline: (optional) absolute deadline.
        period:   (optional) periodic interval.
    """
    def __init__(self,
                 pid,
                 arrival_time,
                 burst_time,
                 deadline=None,
                 period=None):
        self.pid            = pid
        self.arrival_time   = arrival_time
        self.burst_time     = burst_time
        self.remaining_time = burst_time

        # store both, exactly as passed
        self.deadline = deadline
        self.period   = period

        # will be set during scheduling
        self.start_time      = None
        self.completion_time = None
        self.waiting_time    = None
        self.turnaround_time = None

    def __repr__(self):
        return (f"Process(pid={self.pid}, arrival={self.arrival_time}, "
                f"burst={self.burst_time}, deadline={self.deadline}, "
                f"period={self.period})")
