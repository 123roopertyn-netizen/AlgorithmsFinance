"""Saved-results dashboard; starting asset: aif-exercise/assets/dashboard_app.py.

Start: python -m streamlit run 04_dashboard/app.py
Data reads are committed blobs only; no engine or benchmark imports.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from views import main

main()
