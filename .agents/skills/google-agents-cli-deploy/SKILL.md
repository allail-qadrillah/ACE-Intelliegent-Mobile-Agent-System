---
name: google-agents-cli-deploy
description: >-
  Use this skill when deploying or running the ACE Mobile Agent application
  locally. Covers Streamlit startup, virtual environment setup, and
  troubleshooting common deployment issues.
---

# Deploy — Local Deployment

Skill for running and deploying the application locally.

## When to Use
- Setting up the development environment for the first time
- Running the Streamlit application
- Troubleshooting startup errors
- Configuring `.streamlit/config.toml`

## Steps

### 1. Environment Setup
```bash
# Create virtual environment (one-time)
python -m venv .venv

# Activate (Git-Bash)
source .venv/Scripts/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify no conflicts
pip check
```

### 2. Run the Application
```bash
python -m streamlit run app.py
```
The app opens at `http://localhost:8501`.

### 3. Streamlit Configuration
Edit `.streamlit/config.toml` for settings:
- `gatherUsageStats = false` — disable telemetry
- `fileWatcherType = "auto"` — uses watchdog if available

### 4. Troubleshooting
| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Activate `.venv` first |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
| Watchdog conflict | Ensure `watchdog>=6,<7` in requirements.txt |
| `pip check` errors | Re-install: `pip install -r requirements.txt --force-reinstall` |

### 5. Important
- **Do NOT push to GitHub** — deployment is local only.
- All data is synthetic — no credentials or API keys needed.
