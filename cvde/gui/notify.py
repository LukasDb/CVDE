import streamlit as st
from streamlit.runtime import Runtime


def notify(*args: str) -> None:
    message = "".join(args)
    print(message)
    if hasattr(st, "toast"):
        st.toast(message)  # type: ignore
    else:
        st.info(message)


def warn(*args: str) -> None:
    message = "".join(args)
    print(message)
    if hasattr(st, "toast"):
        st.toast(f":color[{message}]")  # type: ignore

    else:
        st.warning(message)


def update_gui_from_thread() -> None:
    runtime: Runtime = Runtime.instance()
    for session in [s.session for s in runtime._session_mgr.list_sessions()]:
        session._handle_rerun_script_request()
