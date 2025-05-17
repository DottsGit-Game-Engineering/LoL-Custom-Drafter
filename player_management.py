import streamlit as st
import database as db
from typing import Optional, Dict
import pandas as pd
import os
import sqlite3
import io
import base64
import requests
from bs4 import BeautifulSoup
import re

def get_champion_list():
    # Try to get from DB, else from CSV
    if 'db_bytes' in st.session_state:
        return db.get_champions()
    else:
        try:
            df = pd.read_csv('champions.csv')
            return df['ChampionName'].dropna().tolist()
        except Exception:
            return []

def show_player_management():
    st.title("Player Management")
    
    # Always load champions at the start so it's available everywhere
    champions = get_champion_list()
    
    # Initialize session state for editing and add player form expansion
    if 'editing_player' not in st.session_state:
        st.session_state.editing_player = None
    if 'show_add_player_form' not in st.session_state:
        st.session_state.show_add_player_form = False
    if 'temp_players' not in st.session_state:
        st.session_state.temp_players = []

    # Collapsible Add New Player Section
    if st.button("Add New Player", key="expand_add_player_form"):
        st.session_state.show_add_player_form = not st.session_state.show_add_player_form

    if st.session_state.show_add_player_form:
        with st.form("add_player_form"):
            name = st.text_input("Player Name")
            rank = st.selectbox("Rank", list(db.RANK_VALUES.keys()))
            
            primary_champion_1 = st.selectbox("Primary Champion", [""] + champions)
            primary_champion_2 = st.selectbox("Secondary Champion", [""] + champions)
            primary_champion_3 = st.selectbox("Third Champion (Optional)", [""] + champions)
            
            notes = st.text_area("Notes (Optional)")
            opgg_link = st.text_input("OP.GG Link (Optional)")
            
            submitted = st.form_submit_button("Add Player")
            if submitted:
                if name:
                    if 'db_bytes' in st.session_state:
                        success = db.add_player(
                            name=name,
                            rank=rank,
                            primary_champion_1=primary_champion_1 if primary_champion_1 else None,
                            primary_champion_2=primary_champion_2 if primary_champion_2 else None,
                            primary_champion_3=primary_champion_3 if primary_champion_3 else None,
                            notes=notes if notes else None,
                            opgg_link=opgg_link if opgg_link else None
                        )
                        if success:
                            st.success(f"Player {name} added successfully!")
                            st.session_state.show_add_player_form = False
                        else:
                            st.error("A player with this name already exists.")
                    else:
                        # Add to temp_players list
                        if any(p['name'] == name for p in st.session_state.temp_players):
                            st.error("A player with this name already exists in the temporary list.")
                        else:
                            st.session_state.temp_players.append({
                                'name': name,
                                'rank': rank,
                                'primary_champion_1': primary_champion_1 if primary_champion_1 else None,
                                'primary_champion_2': primary_champion_2 if primary_champion_2 else None,
                                'primary_champion_3': primary_champion_3 if primary_champion_3 else None,
                                'notes': notes if notes else None,
                                'opgg_link': opgg_link if opgg_link else None
                            })
                            st.success(f"Player {name} added to temporary list!")
                            st.session_state.show_add_player_form = False
                else:
                    st.error("Player name is required.")

    # View/Modify Players Section
    st.header("Current Player List")
    
    # --- Upload DB/CSV file section ---
    if st.session_state.get('db_uploaded', False):
        st.session_state['db_uploaded'] = False
        uploaded_db = None
    else:
        uploaded_db = st.file_uploader(
            "Upload a new player database (.db or .csv)",
            type=["db", "csv"],
            help="This will replace the current player database. Accepts .db or .csv files.",
            accept_multiple_files=False
        )
        if uploaded_db is not None:
            ext = uploaded_db.name.lower().split('.')[-1]
            if ext == 'db':
                # Check file extension
                max_size_mb = 5
                uploaded_db.seek(0, 2)  # Move to end of file
                size_mb = uploaded_db.tell() / (1024 * 1024)
                uploaded_db.seek(0)  # Reset pointer
                if size_mb > max_size_mb:
                    st.error(f"File is too large. Maximum allowed size is {max_size_mb} MB.")
                else:
                    try:
                        db_bytes = uploaded_db.read()
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
            elif ext == 'csv':
                try:
                    df = pd.read_csv(uploaded_db)
                    required_cols = ["name", "rank", "primary_champion_1", "primary_champion_2", "primary_champion_3", "notes"]
                    for col in required_cols:
                        if col not in df.columns:
                            st.error(f"CSV is missing required column: {col}")
                            return
                    # Create new in-memory db and insert data
                    mem_conn = sqlite3.connect(":memory:")
                    mem_conn.row_factory = sqlite3.Row
                    mem_conn.execute('''CREATE TABLE players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        rank TEXT NOT NULL,
                        primary_champion_1 TEXT,
                        primary_champion_2 TEXT,
                        primary_champion_3 TEXT,
                        notes TEXT
                    )''')
                    for _, row in df.iterrows():
                        mem_conn.execute('''INSERT INTO players (name, rank, primary_champion_1, primary_champion_2, primary_champion_3, notes) VALUES (?, ?, ?, ?, ?, ?)''',
                            (row['name'], row['rank'], row['primary_champion_1'], row['primary_champion_2'], row['primary_champion_3'], row['notes']))
                    mem_conn.commit()
                    # Export to bytes using backup (correct way)
                    temp_db_path = "temp_uploaded.db"
                    # Remove temp file if it exists
                    if os.path.exists(temp_db_path):
                        os.remove(temp_db_path)
                    temp_db = sqlite3.connect(temp_db_path)
                    mem_conn.backup(temp_db)
                    temp_db.close()
                    with open(temp_db_path, "rb") as f:
                        csv_db_bytes = f.read()
                    os.remove(temp_db_path)
                    import database
                    database.load_db_file_to_session(csv_db_bytes)
                    st.success("CSV uploaded and loaded into your session as a new database! Reloading...")
                    st.session_state['db_uploaded'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process CSV: {e}")
            else:
                st.error("Only .db or .csv files are allowed.")
    if 'db_bytes' not in st.session_state:
        st.warning("No player database loaded. Players will not be saved permanently. Upload a .db or .csv file to enable full features.")
        # Show temp_players as a DataFrame
        if st.session_state.temp_players:
            df = pd.DataFrame(st.session_state.temp_players)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No players added yet. Use the form above to add players.")
        return

    # --- Export DB button and Update Ranks button ---
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.download_button(
            label="Export Current Database (.db)",
            data=st.session_state['db_bytes'],
            file_name="exported_lol_custom_organizer.db",
            mime="application/octet-stream"
        )
    with col_right:
        if st.button("Update Ranks"):
            update_ranks_from_opgg()

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
                "primary_champion_1": st.column_config.SelectboxColumn("Primary Champion", options=champions),
                "primary_champion_2": st.column_config.SelectboxColumn("Secondary Champion", options=champions),
                "primary_champion_3": st.column_config.SelectboxColumn("Third Champion (Optional)", options=champions),
                "notes": st.column_config.TextColumn("Notes"),
                "opgg_link": st.column_config.TextColumn("OP.GG Link")
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
                        notes=row['notes'] if row['notes'] else None,
                        opgg_link=row['opgg_link'] if 'opgg_link' in row and row['opgg_link'] else None
                    )
                    if success:
                        st.success(f"Player {row['name']} updated successfully!")
                    else:
                        st.error(f"Failed to update player {row['name']}.")
    else:
        st.info("No players added yet. Use the form above to add players.") 

def extract_rank_from_soup(soup):
    import re
    possible_ranks = [
        "Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Master", "Grandmaster", "Challenger"
    ]
    # Regex for valid ranks, case-insensitive
    rank_pattern = re.compile(
        r'^(iron|bronze|silver|gold|platinum|emerald|diamond) [1-4]$|^(master|grandmaster|challenger)$',
        re.IGNORECASE
    )
    for tag in soup.find_all(text=True):
        text = tag.strip()
        if not text:
            continue
        match = rank_pattern.match(text)
        if match:
            # If it's a tier with division (e.g., 'Emerald 1'), return only the tier part
            tier = match.group(1) or match.group(2)
            if tier:
                return tier.title()
            # If it's a top tier (no division), return as is
            return text.title()
    return None

def update_ranks_from_opgg():
    players = db.get_all_players()
    updated = 0
    for player in players:
        opgg_link = player.get('opgg_link')
        if opgg_link:
            try:
                response = requests.get(opgg_link, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Use the robust extraction function
                    rank = extract_rank_from_soup(soup)
                    if rank:
                        # Only update if the rank is valid and different
                        if rank != player['rank']:
                            db.update_player(
                                player_id=player['id'],
                                name=player['name'],
                                rank=rank,
                                primary_champion_1=player['primary_champion_1'],
                                primary_champion_2=player['primary_champion_2'],
                                primary_champion_3=player['primary_champion_3'],
                                notes=player['notes'],
                                opgg_link=player['opgg_link']
                            )
                            updated += 1
                            st.success(f"Updated {player['name']} to {rank}")
                        else:
                            st.info(f"No rank change for {player['name']}")
                    else:
                        st.warning(f"Could not find rank for {player['name']} (check OP.GG link)")
                else:
                    st.error(f"Failed to fetch OP.GG for {player['name']} (HTTP {response.status_code})")
            except Exception as e:
                st.error(f"Error updating {player['name']}: {e}")
    if updated == 0:
        st.info("No ranks were updated.")
    else:
        st.success(f"Ranks updated for {updated} player(s).")
        st.rerun()