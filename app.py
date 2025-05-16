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

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Player Management", "Draft Creator"])

# Main content
if page == "Player Management":
    show_player_management()
else:
    show_draft_creator() 