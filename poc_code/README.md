### Environment Setup
- Forewarning
	- All instructions described below are for a Windows (10/11) machine using git bash
- Install Git Bash
	- [Git/Git Bash installer Download](https://git-scm.com/downloads/win)
- Python Installation
	- Ensure Python >=3.11 is installed
	- [Download Python](https://www.python.org/downloads/)
- Package Management Setup (pip, pipx, and uv)
	- **If you have any questions about uv decision please ask Phillip**
	- pip
		- `pip` should be installed by default with your python installation
	- pipx
		-  Install using `pip install pipx`
	- uv
		- Install using `pipx install uv`

	Run 'pipx ensurepath'

do this in git bash:
- Setting up uv environment (run this in PROJECT_GHOST_SHIELD -> poc_code -> multicast_client)
	- After installing uv run `uv venv --python 3.11`
	- Run `source .venv/Scripts/activate`
	- Your uv venv should now be setup as indicated by the environment name surrounded by parentheses in your terminal ![[Pasted image 20250124145031.png]]