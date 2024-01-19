import streamlit as st


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
