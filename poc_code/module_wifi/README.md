# RF Algorithm – Project Ghost Shield

This module contains the wifi controller logic for Project Ghost Shield. It handles  recieving the IP address of a computer in lattitude and longitude and converting it to Cartesian coordinates (x,y,z) for project use.

---

## Setup Instructions (Using `uv`)

> Requires Python **3.11+** and [`uv`](https://github.com/astral-sh/uv)

### 1. Create a Virtual Environment
```bash
uv venv --python 3.11
```

### 2. Activate the Environment
```bash
source .venv/bin/activate  # macOS/Linux
source .venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

If you're using `pyproject.toml`:
```bash
uv sync
```

---

## Run the Simulation

```bash
cd wifi_lib
uv run wifi_locator.py
```

> This will start the repulsive-force algorithm to space drones equidistantly in a 3D field. It can optionally connect to a GUI via multiprocessing queues if integrated.

---

## Folder Structure

```
module_wifi/
├── wifi_lib/
│   ├── __init__.py
│   ├── wifi_locator.py     # wifi location logic
```

---

## Notes

- You must use Python 3.11+ due to advanced type hints and multiprocessing behavior.


---

## Authors
Phillip Miavelstuck  
Enzo Fernandez  
Sasha Cherian  
Khoi Le  
**George Mason University – Department of Computer Science**