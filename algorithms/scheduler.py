import matplotlib.pyplot as plt
import abc

class Scheduler(abc.ABC):
    """
    Abstract base class for all scheduling algorithms.
    
    Attributes:
        processes: A list of Process instances.
        timeline: A list of tuples recording execution segments:
                  (process id, start time, end time)
    """
    def __init__(self):
        self.processes = []
        self.timeline = []

    def add_process(self, process):
        self.processes.append(process)

    @abc.abstractmethod
    def schedule(self):
        """Perform the scheduling algorithm."""
        pass

    def print_timeline(self):
        """Prints an ASCII Gantt chart for the timeline."""
        if not self.timeline:
            print("No scheduling timeline to display.")
            return

        chart = ""
        time_markers = f"{self.timeline[0][1]:<3}"
        for segment in self.timeline:
            pid, start, end = segment
            width = max(4, int((end - start) * 2))
            block = f" P{pid} ".center(width, '-')
            chart += f"|{block}"
            time_markers += " " * width + f"{end:<3}"
        chart += "|"
        print("Gantt Chart:")
        print(chart)
        print(time_markers)

    def plot_gantt_chart(self, title="Gantt Chart"):
        """Plots the timeline using matplotlib."""
        if not self.timeline:
            print("No timeline data available for plotting.")
            return

        fig, ax = plt.subplots()
        y_labels = []
        for index, segment in enumerate(self.timeline):
            pid, start, end = segment
            duration = end - start
            ax.broken_barh([(start, duration)], (index * 10, 9), facecolors='tab:blue')
            y_labels.append(f"P{pid}")
            ax.text(start + duration/2, index * 10 + 4.5, f"P{pid}",
                    ha='center', va='center', color='white', fontsize=8)
        ax.set_xlabel("Time")
        ax.set_ylabel("Execution Segments")
        ax.set_title(title)
        ax.set_yticks([i * 10 + 4.5 for i in range(len(self.timeline))])
        ax.set_yticklabels(y_labels)
        plt.show()

    def average_waiting_time(self):
        # Treat any None as 0, so sum never sees a None
        total_wait = sum((p.waiting_time if p.waiting_time is not None else 0)
                         for p in self.processes)
        return total_wait / len(self.processes)

    def average_turnaround_time(self):
        # Same for turnaround
        total_tat = sum((p.turnaround_time if p.turnaround_time is not None else 0)
                        for p in self.processes)
        return total_tat / len(self.processes)