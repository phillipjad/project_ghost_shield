# RF Algorithm – Project Ghost Shield

This module contains the core repulsive-force simulation and drone control logic for Project Ghost Shield. It handles drone registration, spatial placement, and inter-drone coordination using multiprocessing.

---

## 📦 Setup Instructions (Using `uv`)

> ✅ Requires Python **3.11+** and [`uv`](https://github.com/astral-sh/uv)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/project_ghost_shield.git
cd project_ghost_shield/rf_algorithm
```

### 2. Create a Virtual Environment
```bash
uv venv --python 3.11
```

### 3. Activate the Environment
```bash
source .venv/bin/activate  # macOS/Linux
source .venv\Scripts\activate     # Windows
```

### 4. Install Dependencies

If you're using `pyproject.toml`:
```bash
uv sync
```

---

## 🚀 Run the Simulation

```bash
uv run rf_simulation.py
```

> This will start the repulsive-force algorithm to space drones equidistantly in a 3D field. It can optionally connect to a GUI via multiprocessing queues if integrated.

---

## 📁 Folder Structure

```
rf_algorithm/
├── controller.py           # Controller logic
├── drone.py                # Drone object and movement
├── field.py                # Drone spacing logic (repulsion)
├── rf_simulation.py        # Simulation orchestrator
├── utils/
│   ├── vector.py
│   ├── distance_obj.py
│   ├── graph_wrapper.py
│   └── read_write_lock.py
```

---

## Notes

- You must use Python 3.11+ due to advanced type hints and multiprocessing behavior.
- GUI integration is handled via `positions_queue` and `drones_queue`, sent from `main.py`.
- Make sure the GUI app is running if you're testing visuals.
- You can modify `space_drones()` in `field.py` to simulate terrain repulsion or other behaviors.

---

## Authors
Phillip Miavelstuck  
Enzo Fernandez  
Sasha Cherian  
Khoi Le  
**George Mason University – Department of Computer Science**
