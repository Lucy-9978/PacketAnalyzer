"""
db_alerts.py

Reusable Streamlit alert system: polls a DB table for new rows and fires
a visual warning + browser TTS announcement when one appears.

Requirements:
    pip install streamlit streamlit-autorefresh

You bring your own DB query function (fetch_latest_fn) — this file is
UI-only, as requested.
"""

import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh


# =========================================================
# CONFIG — edit this to control where alerts are active
# =========================================================
ALERT_CONFIG = {
    # "all"  -> alerts fire on every page that calls watch_table()
    # [...]  -> list of page names where alerts should fire, e.g. ["Home", "Orders"]
    "enabled_pages": "all",

    # how often to check the DB, in milliseconds
    "poll_interval_ms": 5000,

    # message shown/spoken when a new row is found
    # {row} will be replaced with the new row's data
    "message_template": "New entry detected: {row}",

    # toggle TTS on/off globally without removing the visual warning
    "tts_enabled": True,

    # 'toast' (small corner popup), 'warning' (inline banner), or 'both'
    "visual_style": "both",
}


# =========================================================
# Internal helpers
# =========================================================
def _should_alert_on_this_page(page_name: str) -> bool:
    cfg = ALERT_CONFIG["enabled_pages"]
    if cfg == "all":
        return True
    return page_name in cfg


def _speak(text: str):
    """Use the browser's built-in SpeechSynthesis API to read text aloud.
    Note: some browsers block audio until the user has interacted with the
    page at least once (autoplay policy) — a single click anywhere on the
    page beforehand is usually enough."""
    safe_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    components.html(
        f"""
        <script>
        try {{
            const msg = new SpeechSynthesisUtterance("{safe_text}");
            window.speechSynthesis.cancel(); // stop any overlapping speech
            window.speechSynthesis.speak(msg);
        }} catch (e) {{
            console.log("TTS not supported:", e);
        }}
        </script>
        """,
        height=0,
        width=0,
    )


# =========================================================
# Public API
# =========================================================
def watch_table(fetch_latest_fn, get_id_fn=lambda row: row["id"],
                 page_name="all", key="db_watch"):
    """
    Call this once near the top of any page you want alerts on.

    fetch_latest_fn : () -> dict | None
        Your DB function that returns the latest row (e.g. ORDER BY id DESC LIMIT 1).
    get_id_fn : dict -> Any
        Extracts a unique identifier from a row for comparison. Defaults to row["id"].
    page_name : str
        Name of the current page, checked against ALERT_CONFIG["enabled_pages"].
        Pass "all" (default) if you don't care about per-page filtering here,
        or the actual page name (e.g. "Orders") to respect the config list.
    key : str
        Unique key if you call watch_table() multiple times on the same page
        (e.g. watching two different tables).
    """
    if not _should_alert_on_this_page(page_name):
        return

    # Poll on an interval without a full manual page reload
    st_autorefresh(interval=ALERT_CONFIG["poll_interval_ms"], key=f"{key}_autorefresh")

    latest_row = fetch_latest_fn()
    if latest_row is None:
        return

    latest_id = get_id_fn(latest_row)
    state_key = f"{key}_last_id"

    # First run: just record the baseline, don't alert on existing data
    if state_key not in st.session_state:
        st.session_state[state_key] = latest_id
        return

    if latest_id != st.session_state[state_key]:
        st.session_state[state_key] = latest_id
        msg = ALERT_CONFIG["message_template"].format(row=latest_row)

        style = ALERT_CONFIG["visual_style"]
        if style in ("toast", "both"):
            st.toast(msg, icon="⚠️")
        if style in ("warning", "both"):
            st.warning(msg)

        if ALERT_CONFIG["tts_enabled"]:
            _speak(msg)