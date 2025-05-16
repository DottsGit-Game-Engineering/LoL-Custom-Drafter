import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Tuple
import os
import sys
import streamlit as st

# Rank to numerical value mapping
RANK_VALUES = {
    'Iron': 1,
    'Bronze': 2,
    'Silver': 3,
    'Gold': 4,
    'Platinum': 5,
    'Emerald': 6,
    'Diamond': 7,
    'Master': 8,
    'Grandmaster': 9,
    'Challenger': 10
}

def get_db_connection() -> sqlite3.Connection:
    """Create a new in-memory database connection from session DB bytes."""
    if 'db_bytes' not in st.session_state:
        raise RuntimeError("No database loaded for this session. Please upload a .db file.")
    import io
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.row_factory = sqlite3.Row
    with open("temp_uploaded.db", "wb") as tempf:
        tempf.write(st.session_state['db_bytes'])
    tempf = sqlite3.connect("temp_uploaded.db")
    tempf.backup(mem_conn)
    tempf.close()
    return mem_conn

# Utility to load a db file into session state
def load_db_file_to_session(db_bytes: bytes):
    st.session_state['db_bytes'] = db_bytes

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            rank TEXT NOT NULL,
            primary_champion_1 TEXT,
            primary_champion_2 TEXT,
            primary_champion_3 TEXT,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def _update_session_db_bytes(conn):
    import io
    # Save the current in-memory db to bytes and update st.session_state['db_bytes']
    with open("temp_uploaded.db", "wb") as f:
        backup_conn = sqlite3.connect("temp_uploaded.db")
        conn.backup(backup_conn)
        backup_conn.close()
    with open("temp_uploaded.db", "rb") as f:
        st.session_state['db_bytes'] = f.read()

def add_player(name: str, rank: str, primary_champion_1: str = None,
               primary_champion_2: str = None, primary_champion_3: str = None,
               notes: str = None) -> bool:
    """Add a new player to the database."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO players (name, rank, primary_champion_1, primary_champion_2,
                               primary_champion_3, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, rank, primary_champion_1, primary_champion_2,
              primary_champion_3, notes))
        conn.commit()
        _update_session_db_bytes(conn)
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_all_players() -> List[Dict]:
    """Retrieve all players from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players')
    players = [dict(row) for row in c.fetchall()]
    conn.close()
    return players

def update_player(player_id: int, name: str, rank: str,
                 primary_champion_1: str = None, primary_champion_2: str = None,
                 primary_champion_3: str = None, notes: str = None) -> bool:
    """Update an existing player's information."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE players
            SET name = ?, rank = ?, primary_champion_1 = ?, primary_champion_2 = ?,
                primary_champion_3 = ?, notes = ?
            WHERE id = ?
        ''', (name, rank, primary_champion_1, primary_champion_2,
              primary_champion_3, notes, player_id))
        conn.commit()
        _update_session_db_bytes(conn)
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_player(player_id: int) -> bool:
    """Delete a player from the database."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM players WHERE id = ?', (player_id,))
        conn.commit()
        _update_session_db_bytes(conn)
        conn.close()
        return True
    except sqlite3.Error:
        return False

def get_player_by_id(player_id: int) -> Optional[Dict]:
    """Retrieve a specific player by their ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = c.fetchone()
    conn.close()
    return dict(player) if player else None

def get_champions() -> List[str]:
    """Read champion names from champions.csv."""
    try:
        df = pd.read_csv('champions.csv')
        return df['ChampionName'].tolist()
    except FileNotFoundError:
        return []

def get_rank_value(rank: str) -> int:
    """Convert a rank string to its numerical value."""
    return RANK_VALUES.get(rank, 0)

def get_balanced_teams(player_ids: List[int]) -> Tuple[List[Dict], List[Dict]]:
    """Create balanced teams based on player ranks."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get players with their ranks
    players = []
    for player_id in player_ids:
        c.execute('SELECT * FROM players WHERE id = ?', (player_id,))
        player = c.fetchone()
        if player:
            players.append(dict(player))
    
    # Sort players by rank value (descending)
    players.sort(key=lambda x: get_rank_value(x['rank']), reverse=True)
    
    # Initialize teams
    team_a = []
    team_b = []
    team_a_sum = 0
    team_b_sum = 0
    
    # Distribute players
    for player in players:
        if team_a_sum <= team_b_sum:
            team_a.append(player)
            team_a_sum += get_rank_value(player['rank'])
        else:
            team_b.append(player)
            team_b_sum += get_rank_value(player['rank'])
    
    conn.close()
    return team_a, team_b 