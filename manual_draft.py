import streamlit as st
import database as db
import random
from typing import List, Dict

ROLES = ["Top", "Jungle", "Mid", "ADC", "Support"]

def show_manual_draft():
    st.title("Manual Team Draft")
    st.sidebar.header("Manual Draft Configuration")
    num_bans = st.sidebar.number_input("Number of Bans to Select from Pool", min_value=0, max_value=20, value=10, key="manual_num_bans")
    additional_random_bans = st.sidebar.number_input("Number of Additional Random Bans", min_value=0, max_value=10, value=0, key="manual_additional_random_bans")

    # Step 1: Select Players (same as draft_creator)
    st.header("Step 1: Select Players")
    if 'db_bytes' not in st.session_state:
        st.warning("No player database loaded. Please upload a .db file in the Player Management page to begin.")
        return
    players = db.get_all_players()
    if not players:
        st.error("No players available. Please add players in the Player Management page.")
        return
    player_names = [player['name'] for player in players]
    selected_names = st.multiselect(
        "Select 10 Players",
        player_names,
        max_selections=10,
        key="manual_selected_players"
    )
    if len(selected_names) == 10:
        selected_players = [p for p in players if p['name'] in selected_names]
        st.session_state.manual_selected_players_objs = selected_players
        st.success("10 players selected!")
    else:
        st.warning(f"Please select exactly 10 players. Currently selected: {len(selected_names)}")
        st.session_state.manual_selected_players_objs = []

    # Step 2: Captain Selection
    if st.session_state.get('manual_selected_players_objs'):
        st.header("Step 2: Select Captains")
        player_names = [p['name'] for p in st.session_state.manual_selected_players_objs]
        # Handle randomization before widgets are created
        if st.session_state.get('manual_randomize_captains', False):
            random_captains = random.sample(player_names, 2)
            st.session_state.manual_team_a_captain = random_captains[0]
            st.session_state.manual_team_b_captain = random_captains[1]
            st.session_state.manual_randomize_captains = False
        col1, col2 = st.columns(2)
        with col1:
            team_a_captain = st.selectbox("Select Team A Captain", player_names, key="manual_team_a_captain")
        with col2:
            team_b_captain = st.selectbox("Select Team B Captain", [n for n in player_names if n != team_a_captain], key="manual_team_b_captain")
        if st.button("Randomly Select Captains"):
            st.session_state.manual_randomize_captains = True
            st.rerun()

    # Step 3: Manual Drafting
    if st.session_state.get('manual_selected_players_objs') and 'team_a_captain' in locals() and 'team_b_captain' in locals():
        st.header("Step 3: Draft Teams")
        # Ensure team and pool lists are always initialized and always reflect current captains if only captains are present
        just_captains = (
            len(st.session_state.get('manual_team_a', [])) <= 1 and
            len(st.session_state.get('manual_team_b', [])) <= 1 and
            len(st.session_state.get('manual_player_pool', [])) >= 8
        )
        if (
            'manual_team_a' not in st.session_state or
            'manual_team_b' not in st.session_state or
            'manual_player_pool' not in st.session_state or
            just_captains or
            (st.session_state.manual_team_a and st.session_state.manual_team_a[0]['name'] != team_a_captain) or
            (st.session_state.manual_team_b and st.session_state.manual_team_b[0]['name'] != team_b_captain)
        ):
            st.session_state.manual_team_a = [p for p in st.session_state.manual_selected_players_objs if p['name'] == team_a_captain]
            st.session_state.manual_team_b = [p for p in st.session_state.manual_selected_players_objs if p['name'] == team_b_captain]
            st.session_state.manual_player_pool = [p for p in st.session_state.manual_selected_players_objs if p['name'] not in [team_a_captain, team_b_captain]]
        # Add custom CSS for columns and animation
        st.markdown(
            '''
            <style>
            .team-col {
                background: #e3f2fd;
                border: 2px solid #1976d2;
                border-radius: 12px;
                padding: 18px 12px 12px 12px;
                margin-bottom: 8px;
                min-height: 320px;
                box-shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
                transition: box-shadow 0.3s;
            }
            .team-col.team-b {
                background: #fce4ec;
                border-color: #d81b60;
                box-shadow: 0 2px 8px rgba(216, 27, 96, 0.08);
            }
            .team-col.available {
                background: #f3e5f5;
                border-color: #7b1fa2;
                box-shadow: 0 2px 8px rgba(123, 31, 162, 0.08);
            }
            .player-flash {
                animation: flash 0.7s;
            }
            @keyframes flash {
                0% { background: #fffde7; }
                50% { background: #fff176; }
                100% { background: inherit; }
            }
            </style>
            ''', unsafe_allow_html=True)
        # Animate if a player was just added
        flash_a = st.session_state.pop('manual_flash_a', None)
        flash_b = st.session_state.pop('manual_flash_b', None)
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            # Build Team A HTML block
            team_a_html = f'<div class="team-col">'
            team_a_html += '<h3 style="margin-top:0">Team A</h3>'
            for p in st.session_state.manual_team_a:
                flash_class = " player-flash" if flash_a == p['name'] else ""
                team_a_html += f'<div class="{flash_class}">{"• <b>" if p["name"] == team_a_captain else "• "}{p["name"]} ({p["rank"]}){" (Captain)</b>" if p["name"] == team_a_captain else ""}</div>'
            team_a_html += '</div>'
            st.markdown(team_a_html, unsafe_allow_html=True)
            if st.session_state.manual_player_pool and len(st.session_state.manual_team_a) < 5:
                pick = st.selectbox("Add to Team A", [p['name'] for p in st.session_state.manual_player_pool], key="manual_pick_a")
                if st.button("Add to Team A", key="manual_add_a"):
                    player = next(p for p in st.session_state.manual_player_pool if p['name'] == pick)
                    st.session_state.manual_team_a.append(player)
                    st.session_state.manual_player_pool = [p for p in st.session_state.manual_player_pool if p['name'] != pick]
                    st.session_state.manual_flash_a = pick
                    st.rerun()
        with col2:
            # Build Available Players HTML block
            avail_html = f'<div class="team-col available">'
            avail_html += '<h3 style="margin-top:0">Available Players</h3>'
            for p in st.session_state.manual_player_pool:
                avail_html += f'<div>• {p["name"]} ({p["rank"]})</div>'
            avail_html += '</div>'
            st.markdown(avail_html, unsafe_allow_html=True)
        with col3:
            # Build Team B HTML block
            team_b_html = f'<div class="team-col team-b">'
            team_b_html += '<h3 style="margin-top:0">Team B</h3>'
            for p in st.session_state.manual_team_b:
                flash_class = " player-flash" if flash_b == p['name'] else ""
                team_b_html += f'<div class="{flash_class}">{"• <b>" if p["name"] == team_b_captain else "• "}{p["name"]} ({p["rank"]}){" (Captain)</b>" if p["name"] == team_b_captain else ""}</div>'
            team_b_html += '</div>'
            st.markdown(team_b_html, unsafe_allow_html=True)
            if st.session_state.manual_player_pool and len(st.session_state.manual_team_b) < 5:
                pick = st.selectbox("Add to Team B", [p['name'] for p in st.session_state.manual_player_pool], key="manual_pick_b")
                if st.button("Add to Team B", key="manual_add_b"):
                    player = next(p for p in st.session_state.manual_player_pool if p['name'] == pick)
                    st.session_state.manual_team_b.append(player)
                    st.session_state.manual_player_pool = [p for p in st.session_state.manual_player_pool if p['name'] != pick]
                    st.session_state.manual_flash_b = pick
                    st.rerun()
        # Reset draft
        if st.button("Reset Draft Teams"):
            st.session_state.manual_team_a = [p for p in st.session_state.manual_selected_players_objs if p['name'] == team_a_captain]
            st.session_state.manual_team_b = [p for p in st.session_state.manual_selected_players_objs if p['name'] == team_b_captain]
            st.session_state.manual_player_pool = [p for p in st.session_state.manual_selected_players_objs if p['name'] not in [team_a_captain, team_b_captain]]
            st.rerun()

    # Step 4: Role Selection
    if len(st.session_state.get('manual_team_a', [])) == 5 and len(st.session_state.get('manual_team_b', [])) == 5:
        st.header("Step 4: Assign Roles")
        if 'manual_team_a_roles' not in st.session_state:
            st.session_state.manual_team_a_roles = {}
        if 'manual_team_b_roles' not in st.session_state:
            st.session_state.manual_team_b_roles = {}
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Team A Roles")
            for p in st.session_state.manual_team_a:
                role = st.selectbox(
                    f"Role for {p['name']}",
                    ["Not assigned"] + ROLES,
                    index=(1 + ROLES.index(st.session_state.manual_team_a_roles[p['name']]) if p['name'] in st.session_state.manual_team_a_roles and st.session_state.manual_team_a_roles[p['name']] in ROLES else 0),
                    key=f"manual_role_a_{p['name']}"
                )
                if role != "Not assigned":
                    st.session_state.manual_team_a_roles[p['name']] = role
                elif p['name'] in st.session_state.manual_team_a_roles:
                    del st.session_state.manual_team_a_roles[p['name']]
            # Check for duplicate roles
            assigned_roles = [r for r in st.session_state.manual_team_a_roles.values() if r != "Not assigned"]
            if len(set(assigned_roles)) < len(assigned_roles):
                st.warning("Duplicate roles assigned in Team A!")
            if st.button("Randomize Team A Roles"):
                roles = ROLES.copy()
                random.shuffle(roles)
                st.session_state.manual_team_a_roles = {p['name']: role for p, role in zip(st.session_state.manual_team_a, roles)}
                st.rerun()
        with col2:
            st.subheader("Team B Roles")
            for p in st.session_state.manual_team_b:
                role = st.selectbox(
                    f"Role for {p['name']}",
                    ["Not assigned"] + ROLES,
                    index=(1 + ROLES.index(st.session_state.manual_team_b_roles[p['name']]) if p['name'] in st.session_state.manual_team_b_roles and st.session_state.manual_team_b_roles[p['name']] in ROLES else 0),
                    key=f"manual_role_b_{p['name']}"
                )
                if role != "Not assigned":
                    st.session_state.manual_team_b_roles[p['name']] = role
                elif p['name'] in st.session_state.manual_team_b_roles:
                    del st.session_state.manual_team_b_roles[p['name']]
            # Check for duplicate roles
            assigned_roles = [r for r in st.session_state.manual_team_b_roles.values() if r != "Not assigned"]
            if len(set(assigned_roles)) < len(assigned_roles):
                st.warning("Duplicate roles assigned in Team B!")
            if st.button("Randomize Team B Roles"):
                roles = ROLES.copy()
                random.shuffle(roles)
                st.session_state.manual_team_b_roles = {p['name']: role for p, role in zip(st.session_state.manual_team_b, roles)}
                st.rerun()
        # Reset roles
        if st.button("Reset Roles"):
            st.session_state.manual_team_a_roles = {}
            st.session_state.manual_team_b_roles = {}
            st.rerun()

    # Step 5: Ban Phase
    if len(st.session_state.get('manual_team_a_roles', {})) == 5 and len(st.session_state.get('manual_team_b_roles', {})) == 5:
        st.header("Step 5: Ban Phase")
        if 'manual_banned_champions' not in st.session_state:
            st.session_state.manual_banned_champions = []
        if st.button("Generate Bans"):
            # Collect all primary champions from both teams
            all_players = st.session_state.manual_team_a + st.session_state.manual_team_b
            potential_bans = set()
            for player in all_players:
                for champ in [player['primary_champion_1'], player['primary_champion_2'], player['primary_champion_3']]:
                    if champ:
                        potential_bans.add(champ)
            potential_bans = list(potential_bans)
            random.shuffle(potential_bans)
            bans = potential_bans[:num_bans]
            if additional_random_bans > 0:
                all_champions = db.get_champions()
                available_champions = [champ for champ in all_champions if champ not in bans]
                random.shuffle(available_champions)
                bans.extend(available_champions[:additional_random_bans])
            st.session_state.manual_banned_champions = bans
        if st.session_state.manual_banned_champions:
            st.subheader("Banned Champions")
            for champ in st.session_state.manual_banned_champions:
                st.write(f"• {champ}")
        if st.button("Reset Bans"):
            st.session_state.manual_banned_champions = []
            st.rerun()
    # Reset all
    if st.button("Start New Manual Draft"):
        for key in [
            'manual_selected_players_objs', 'manual_team_a_captain', 'manual_team_b_captain',
            'manual_team_a', 'manual_team_b', 'manual_player_pool',
            'manual_team_a_roles', 'manual_team_b_roles', 'manual_banned_champions']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun() 