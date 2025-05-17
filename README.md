# Scheduling Simulator

A Python-based scheduling simulator supporting multiple algorithms: FCFS, SJN, Round Robin, Rate Monotonic, and Earliest Deadline First (EDF). Offers both command-line and Pygame graphical interfaces.

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

### Command-Line Interface (CLI)

```bash
python main.py
```

* When prompted, enter `1` to launch the CLI.
* Follow on-screen instructions to select an algorithm, input or generate processes, and view results.

### Pygame Graphical Interface

```bash
python main.py
```

* When prompted, enter `2` to launch the Pygame window.
* Click on algorithm cards, choose random or custom processes, and step through simulations.

---

## File Structure

* `main.py` — Entry point; contains both CLI and Pygame interfaces
* `algorithms/` — Scheduling implementations (FCFS, SJN, RR, RM, EDF)
* `ui/` — Fonts and card UI components
* `components/` — Table, GanttChart, BarChart, Container classes
* `requirements.txt` — Python dependencies

---
