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
tab_objs = st.tabs(TABS)

with tab_objs[0]:
    show_player_management()
with tab_objs[1]:
    show_draft_creator() 