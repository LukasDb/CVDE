import streamlit as st
from typing import Any

import cvde
from cvde.workspace import Workspace as WS


class DataExplorer:
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        if "data_index" not in st.session_state:
            st.session_state["data_index"] = 0

        data_loaders = [x.__name__ for x in WS().datasets]
        configs = WS().list_configs()

        # build data viewer
        col1, col2, col3 = st.columns(3)
        dataset_name = col1.selectbox("Data source", data_loaders, on_change=self.reset)
        config_name = col2.selectbox("Config", configs, on_change=self.reset)
        if config_name is None:
            return

        # reloads page, progresses through iterable dataset
        buttons = col3.columns(3)
        buttons[0].button("Prev", on_click=self.dec_data_index)
        buttons[1].button("Next", on_click=self.inc_data_index)
        buttons[2].button("Reset", on_click=self.reset)

        config = cvde.ws_tools.load_config(config_name)
        config = config.get(dataset_name, {})

        if dataset_name is None:
            return

        if "loaded_dataset" not in st.session_state:
            with st.spinner("Loading dataset..."):
                dataset_fn = cvde.ws_tools.load_dataset(dataset_name)
                dataset = dataset_fn(**config)
            st.session_state["loaded_dataset"] = dataset
        else:
            dataset = st.session_state["loaded_dataset"]

        data = self.get_data(dataset, int(st.session_state.data_index))

        st.subheader(f"#{st.session_state.data_index}", anchor=False)
        dataset.visualize_example(data)

    @st.cache_data(show_spinner="Loading data...")
    def get_data(_self, _dataset: cvde.Dataset, data_index: int) -> Any:
        return _dataset[data_index]

    def inc_data_index(self) -> None:
        st.session_state.data_index += 1

    def dec_data_index(self) -> None:
        st.session_state.data_index -= 1

    def reset(self) -> None:
        if "loaded_dataset" in st.session_state:
            del st.session_state["loaded_dataset"]
        st.cache_data.clear()
        st.session_state.data_index = 0
