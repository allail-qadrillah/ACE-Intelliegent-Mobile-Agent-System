"""Memastikan paket ``hotel_demo`` dapat diimpor dari mana pun pytest dijalankan."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
