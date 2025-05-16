import streamlit as st
import database as db
import random
from typing import List, Dict, Tuple

# Define roles
ROLES = ["Top", "Jungle", "Mid", "ADC", "Support"]

def initialize_session_state(team_rerolls=2, role_rerolls=2):
    """Initialize session state variables with reroll counts."""
    st.session_state.selected_players = []
    st.session_state.team_a = []
    st.session_state.team_b = []
    st.session_state.team_a_roles = {}
    st.session_state.team_b_roles = {}
    st.session_state.banned_champions = []
    st.session_state.team_rerolls = team_rerolls
    st.session_state.role_rerolls_a = role_rerolls
    st.session_state.role_rerolls_b = role_rerolls

def randomize_roles(team: List[Dict]) -> Dict[str, str]:
    """Randomly assign roles to team members."""
    roles = ROLES.copy()
    random.shuffle(roles)
    return {player['name']: role for player, role in zip(team, roles)}

def reroll_team_a_roles():
    if st.session_state.role_rerolls_a > 0:
        st.session_state.team_a_roles = randomize_roles(st.session_state.team_a)
        st.session_state.role_rerolls_a -= 1

def reroll_team_b_roles():
    if st.session_state.role_rerolls_b > 0:
        st.session_state.team_b_roles = randomize_roles(st.session_state.team_b)
        st.session_state.role_rerolls_b -= 1

def generate_bans(players: List[Dict], num_bans: int, additional_random_bans: int = 0) -> List[str]:
    """Generate champion bans from players' primary champions."""
    # Collect all primary champions
    potential_bans = set()
    for player in players:
        for champ in [player['primary_champion_1'], player['primary_champion_2'], player['primary_champion_3']]:
            if champ:
                potential_bans.add(champ)
    
    # Convert to list and shuffle
    potential_bans = list(potential_bans)
    random.shuffle(potential_bans)
    
    # Select bans from primary champions
    bans = potential_bans[:num_bans]
    
    # Add random bans if requested
    if additional_random_bans > 0:
        all_champions = db.get_champions()
        available_champions = [champ for champ in all_champions if champ not in bans]
        random.shuffle(available_champions)
        bans.extend(available_champions[:additional_random_bans])
    
    return bans

def show_draft_creator():
    st.title("Custom Game Draft Creator")
    
    # Configuration Settings
    st.sidebar.header("Configuration")
    num_bans = st.sidebar.number_input("Number of Bans to Select from Pool", min_value=0, max_value=20, value=10)
    skill_balancing = st.sidebar.checkbox("Attempt Skill Balancing for Teams", value=True)
    max_team_rerolls = st.sidebar.number_input("Max Team Rerolls Allowed", min_value=0, max_value=5, value=2)
    max_role_rerolls = st.sidebar.number_input("Max Role Rerolls Per Team", min_value=0, max_value=5, value=2)
    additional_random_bans = st.sidebar.number_input("Number of Additional Random Bans", min_value=0, max_value=10, value=0)
    
    # Initialize session state if not present
    if 'team_rerolls' not in st.session_state or 'role_rerolls_a' not in st.session_state or 'role_rerolls_b' not in st.session_state:
        initialize_session_state(max_team_rerolls, max_role_rerolls)
    
    # Step 1: Select Players
    st.header("Step 1: Select Players")
    players = db.get_all_players()
    if not players:
        st.error("No players available. Please add players in the Player Management page.")
        return
    
    player_names = [player['name'] for player in players]
    selected_names = st.multiselect(
        "Select 10 Players",
        player_names,
        max_selections=10
    )
    
    if len(selected_names) == 10:
        st.session_state.selected_players = [p for p in players if p['name'] in selected_names]
        st.success("10 players selected!")
    else:
        st.warning(f"Please select exactly 10 players. Currently selected: {len(selected_names)}")
    
    # Step 2: Team Randomization
    if st.session_state.selected_players:
        st.header("Step 2: Team Randomization")
        can_reroll = st.session_state.team_rerolls > 0
        button_label = "Randomize Teams" if not st.session_state.team_a and not st.session_state.team_b else f"Reroll Teams ({st.session_state.team_rerolls} remaining)"
        st.info(f"Team rerolls remaining: {st.session_state.team_rerolls}")
        if st.button(button_label, disabled=not can_reroll):
            if skill_balancing:
                st.session_state.team_a, st.session_state.team_b = db.get_balanced_teams(
                    [p['id'] for p in st.session_state.selected_players]
                )
            else:
                players = st.session_state.selected_players.copy()
                random.shuffle(players)
                st.session_state.team_a = players[:5]
                st.session_state.team_b = players[5:]
            st.session_state.team_rerolls -= 1
            st.session_state.team_a_roles = {}
            st.session_state.team_b_roles = {}
            st.session_state.banned_champions = []
            st.session_state.role_rerolls_a = max_role_rerolls
            st.session_state.role_rerolls_b = max_role_rerolls
        
        # Display teams
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Team A")
            for player in st.session_state.team_a:
                st.write(f"• {player['name']} ({player['rank']})")
        
        with col2:
            st.subheader("Team B")
            for player in st.session_state.team_b:
                st.write(f"• {player['name']} ({player['rank']})")
    
    # Step 3: Role Assignment
    if st.session_state.team_a and st.session_state.team_b:
        st.header("Step 3: Role Assignment")
        if not st.session_state.team_a_roles:
            if st.button("Randomize All Roles", key="randomize_all_roles"):
                st.session_state.team_a_roles = randomize_roles(st.session_state.team_a)
                st.session_state.team_b_roles = randomize_roles(st.session_state.team_b)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Team A Roles")
            for player in st.session_state.team_a:
                role = st.session_state.team_a_roles.get(player['name'], "Not assigned")
                st.write(f"• {player['name']}: {role}")
            st.button(
                f"Reroll Team A Roles ({st.session_state.role_rerolls_a} remaining)",
                key="reroll_team_a",
                disabled=st.session_state.role_rerolls_a <= 0,
                on_click=reroll_team_a_roles
            )
        with col2:
            st.subheader("Team B Roles")
            for player in st.session_state.team_b:
                role = st.session_state.team_b_roles.get(player['name'], "Not assigned")
                st.write(f"• {player['name']}: {role}")
            st.button(
                f"Reroll Team B Roles ({st.session_state.role_rerolls_b} remaining)",
                key="reroll_team_b",
                disabled=st.session_state.role_rerolls_b <= 0,
                on_click=reroll_team_b_roles
            )
    
    # Step 4: Ban Phase
    if st.session_state.team_a_roles and st.session_state.team_b_roles:
        st.header("Step 4: Ban Phase")
        
        if not st.session_state.banned_champions:
            if st.button("Generate Bans"):
                st.session_state.banned_champions = generate_bans(
                    st.session_state.selected_players,
                    num_bans,
                    additional_random_bans
                )
        
        if st.session_state.banned_champions:
            st.subheader("Banned Champions")
            for champ in st.session_state.banned_champions:
                st.write(f"• {champ}")
    
    # Reset Button
    if st.button("Start New Draft"):
        initialize_session_state(max_team_rerolls, max_role_rerolls)
        st.experimental_rerun()

    # --- Handle pending reroll actions (fix double-click issue) ---
    if 'pending_reroll_a' in st.session_state:
        del st.session_state['pending_reroll_a']
    if 'pending_reroll_b' in st.session_state:
        del st.session_state['pending_reroll_b'] 