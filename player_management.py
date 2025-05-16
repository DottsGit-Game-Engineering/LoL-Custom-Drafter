import streamlit as st
import database as db
from typing import Optional, Dict
import pandas as pd
import os

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
    
    # --- Upload DB file section ---
    if st.session_state.get('db_uploaded', False):
        st.session_state['db_uploaded'] = False
        uploaded_db = None
    else:
        uploaded_db = st.file_uploader(
            "Upload a new player database (.db)",
            type=["db"],
            help="This will replace the current player database.",
            accept_multiple_files=False
        )
        if uploaded_db is not None:
            # Check file extension
            if not uploaded_db.name.lower().endswith('.db'):
                st.error("Only .db files are allowed.")
            else:
                max_size_mb = 5
                uploaded_db.seek(0, 2)  # Move to end of file
                size_mb = uploaded_db.tell() / (1024 * 1024)
                uploaded_db.seek(0)  # Reset pointer
                if size_mb > max_size_mb:
                    st.error(f"File is too large. Maximum allowed size is {max_size_mb} MB.")
                else:
                    try:
                        db_bytes = uploaded_db.read()
                        import sqlite3
                        # Validate the uploaded DB has the 'players' table
                        mem_conn = sqlite3.connect(":memory:")
                        mem_conn.row_factory = sqlite3.Row
                        with open("temp_uploaded.db", "wb") as tempf:
                            tempf.write(db_bytes)
                        tempf = sqlite3.connect("temp_uploaded.db")
                        try:
                            tempf.execute("SELECT 1 FROM players LIMIT 1")
                            tempf.close()
                            # Load into session
                            import database
                            database.load_db_file_to_session(db_bytes)
                            st.success("Database uploaded and loaded into your session! Reloading...")
                            st.session_state['db_uploaded'] = True
                            st.rerun()
                        except Exception as e:
                            tempf.close()
                            st.error(f"Uploaded database is invalid or missing the 'players' table: {e}")
                    except Exception as e:
                        st.error(f"Failed to upload database: {e}")
    if 'db_bytes' not in st.session_state:
        st.warning("No player database loaded. Please upload a .db file to begin.")
        return
    
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