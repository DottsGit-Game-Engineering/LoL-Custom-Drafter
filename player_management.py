import streamlit as st
import database as db
from typing import Optional, Dict
import pandas as pd

def show_player_management():
    st.title("Player Management")
    
    # Initialize session state for editing
    if 'editing_player' not in st.session_state:
        st.session_state.editing_player = None
    
    # Add New Player Section
    st.header("Add New Player")
    with st.form("add_player_form"):
        name = st.text_input("Player Name")
        rank = st.selectbox("Rank", list(db.RANK_VALUES.keys()))
        
        champions = db.get_champions()
        primary_champion_1 = st.selectbox("Primary Champion 1", [""] + champions)
        primary_champion_2 = st.selectbox("Primary Champion 2", [""] + champions)
        primary_champion_3 = st.selectbox("Primary Champion 3 (Optional)", [""] + champions)
        
        notes = st.text_area("Notes (Optional)")
        
        submitted = st.form_submit_button("Add Player")
        if submitted:
            if name:
                success = db.add_player(
                    name=name,
                    rank=rank,
                    primary_champion_1=primary_champion_1 if primary_champion_1 else None,
                    primary_champion_2=primary_champion_2 if primary_champion_2 else None,
                    primary_champion_3=primary_champion_3 if primary_champion_3 else None,
                    notes=notes if notes else None
                )
                if success:
                    st.success(f"Player {name} added successfully!")
                else:
                    st.error("A player with this name already exists.")
            else:
                st.error("Player name is required.")
    
    # View/Modify Players Section
    st.header("Current Player List")
    players = db.get_all_players()
    
    if players:
        # Create a DataFrame for display
        df = pd.DataFrame(players)
        df = df.drop('id', axis=1)  # Don't show ID in the table
        
        # Display the table with editing capabilities
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "name": st.column_config.TextColumn("Name", required=True),
                "rank": st.column_config.SelectboxColumn("Rank", options=list(db.RANK_VALUES.keys()), required=True),
                "primary_champion_1": st.column_config.SelectboxColumn("Primary Champion 1", options=champions),
                "primary_champion_2": st.column_config.SelectboxColumn("Primary Champion 2", options=champions),
                "primary_champion_3": st.column_config.SelectboxColumn("Primary Champion 3", options=champions),
                "notes": st.column_config.TextColumn("Notes")
            }
        )
        
        # Handle updates
        if edited_df is not None:
            for idx, row in edited_df.iterrows():
                player = players[idx]
                if row.to_dict() != {k: v for k, v in player.items() if k != 'id'}:
                    success = db.update_player(
                        player_id=player['id'],
                        name=row['name'],
                        rank=row['rank'],
                        primary_champion_1=row['primary_champion_1'] if row['primary_champion_1'] else None,
                        primary_champion_2=row['primary_champion_2'] if row['primary_champion_2'] else None,
                        primary_champion_3=row['primary_champion_3'] if row['primary_champion_3'] else None,
                        notes=row['notes'] if row['notes'] else None
                    )
                    if success:
                        st.success(f"Player {row['name']} updated successfully!")
                    else:
                        st.error(f"Failed to update player {row['name']}.")
    else:
        st.info("No players added yet. Use the form above to add players.") 