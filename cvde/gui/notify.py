import streamlit as st


def notify(*args):
    message = "".join(args)
    print(message)
    if hasattr(st, "toast"):
        st.toast(message)
    else:
        st.info(message)


def warn(*args):
    message = "".join(args)
    print(message)
    if hasattr(st, "toast"):
        st.toast(f":color[{message}]")

    else:
        st.warning(message)
