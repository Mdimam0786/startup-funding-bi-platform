"""
Error handling utilities. Every data-loading or model-loading call in
this app goes through safe_run so a missing file or corrupt CSV shows a
clean, on-brand error state instead of Streamlit's raw traceback.
"""
import functools
import traceback

import streamlit as st

from utils.logger import get_logger

log = get_logger("error_handler")


def safe_run(fallback_message: str = "Something went wrong loading this section."):
    """Decorator: catches exceptions, logs the full traceback, shows a clean UI message."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                log.error(f"{func.__name__} - missing file: {e}")
                render_error(
                    "Data file not found",
                    f"{fallback_message} A required data file is missing: `{e.filename if hasattr(e, 'filename') else e}`.",
                )
            except Exception as e:
                log.error(f"{func.__name__} failed: {e}\n{traceback.format_exc()}")
                render_error("Unexpected error", f"{fallback_message} ({type(e).__name__}: {e})")
        return wrapper
    return decorator


def render_error(title: str, message: str):
    st.markdown(
        f"""
        <div class="app-card" style="border-color: var(--danger);">
            <div style="display:flex; align-items:center; gap:0.6rem;">
                <span style="font-size:1.3rem;">⚠</span>
                <strong style="color: var(--danger);">{title}</strong>
            </div>
            <p class="subtle" style="margin-top:0.5rem; margin-bottom:0;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
