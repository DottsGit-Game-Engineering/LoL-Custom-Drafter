import streamlit as st
import database as db
from player_management import show_player_management
from draft_creator import show_draft_creator

# Set page config
st.set_page_config(
    page_title="LoL Custom Game Organizer",
    page_icon="🎮",
    layout="wide"
)

# Tab navigation at the top
TABS = ["Player Management", "Draft Creator"]

# Use st.query_params to track the active tab (for future extensibility, but not for sidebar logic)
query_params = st.query_params

# Use st.tabs to get the selected tab
tab_objs = st.tabs(TABS)

with tab_objs[0]:
    # Hide the sidebar only on this tab
    st.markdown(
        """
        <style>
        [data-testid=\"stSidebar\"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
    show_player_management()
with tab_objs[1]:
    # Show the sidebar only on this tab
    st.markdown(
        """
        <style>
        [data-testid=\"stSidebar\"] { display: block !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
    show_draft_creator() 