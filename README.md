# League of Legends Custom Game Organizer

A Streamlit application for organizing custom League of Legends games with features for player management, team balancing, role assignment, and champion bans.

## Features

- Player Management: Add, edit, and delete players with their ranks and primary champions
- Team Randomization: Create balanced teams based on player ranks
- Role Assignment: Randomly assign roles to players
- Champion Bans: Generate random bans from players' primary champions

## Web Hosted by Streamlit
Here is a publicly available web hosted version of the tool if you don't want to set it up locally.

https://lol-custom-drafter.streamlit.app/

## Local Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```

## File Structure

- `app.py`: Main application entry point
- `player_management.py`: Player management page
- `draft_creator.py`: Draft creation page
- `database.py`: Database operations
- `champions.csv`: List of League of Legends champions
- `requirements.txt`: Project dependencies

## Database

The application uses SQLite for data storage. The database file (`lol_custom_organizer.db`) will be created automatically when you first run the application. 
