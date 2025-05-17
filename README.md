# Scheduling Simulator

A Python-based scheduling simulator supporting multiple algorithms: FCFS, SJN, Round Robin, Rate Monotonic, and Earliest Deadline First (EDF). Offers Pygame graphical interface.

---

## Prerequisites

* Python 3.8 or newer
* A POSIX shell (Linux/macOS) or PowerShell/Command Prompt (Windows)
* `requirements.txt` provided in project root

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/RusaUB/algo-scheduler.git
   cd algo-scheduler
   ```

2. **Create a virtual environment**

   * macOS/Linux:

     ```bash
     python3 -m venv env
     source env/bin/activate
     ```

   * Windows (PowerShell):

     ```powershell
     python -m venv env
     .\env\Scripts\Activate.ps1
     ```

   * Windows (Cmd.exe):

     ```cmd
     python -m venv env
     env\Scripts\activate
     ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Usage

From the project root, with the virtual environment activated:


### Pygame Graphical Interface

```bash
python main.py
```


Click on algorithm cards, choose random or custom processes, and step through simulations.

---

## File Structure

* `main.py` — Entry point; contains Pygame interface
* `algorithms/` — Scheduling implementations (FCFS, SJN, RR, RM, EDF)
* `ui/` — Fonts and card UI components
* `components/` — Table, GanttChart, BarChart, Container classes
* `requirements.txt` — Python dependencies

---
