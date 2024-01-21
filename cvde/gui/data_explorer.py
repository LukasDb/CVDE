import streamlit as st
import cvde
from .page import Page


class DataExplorer(Page):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        if "data_index" not in st.session_state:
            st.session_state["data_index"] = 0

        datasets: dict[str, type[cvde.tf.Dataset]] = cvde.Workspace().list_datasets()
        configs = cvde.Workspace().list_configs()

        # build data viewer
        col1, col2, col3 = st.columns(3)
        dataset_name = col1.selectbox(
            "Data source", list(datasets.keys()), on_change=self.clear_cache
        )
        config_name = col2.selectbox("Config", list(configs.keys()), on_change=self.clear_cache)
        if config_name is None:
            return

        # reloads page, progresses through iterable dataset
        buttons = col3.columns(3)
        buttons[0].button("Prev", on_click=self.dec_data_index)
        buttons[1].button("Next", on_click=self.inc_data_index)
        buttons[2].button("Reset", on_click=self.clear_cache)

        config = configs[config_name]
        config = config.get(dataset_name, {})

        if dataset_name is None:
            return

        if "loaded_dataset" not in st.session_state:
            with st.spinner("Loading dataset..."):
                dataset = datasets[dataset_name](**config)
            st.session_state["loaded_dataset"] = dataset
        else:
            dataset = st.session_state["loaded_dataset"]

        data = dataset[st.session_state.data_index]

        st.subheader(f"#{st.session_state.data_index}", anchor=False)
        dataset.visualize_example(data)

    def on_leave(self) -> None:
        if "loaded_dataset" in st.session_state:
            del st.session_state["loaded_dataset"]
        return super().on_leave()

    def inc_data_index(self) -> None:
        st.session_state.data_index += 1

    def dec_data_index(self) -> None:
        st.session_state.data_index -= 1

    def clear_cache(self) -> None:
        if "loaded_dataset" in st.session_state:
            del st.session_state["loaded_dataset"]
        st.cache_data.clear()
        st.session_state.data_index = 0
