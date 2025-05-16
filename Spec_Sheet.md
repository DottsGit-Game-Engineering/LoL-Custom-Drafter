\# League of Legends Custom Game Organizer \- Application Specification

\#\# 1\. Overview

This application will allow users to manage a list of League of Legends players, their ranks, and their primary champions. It will then facilitate the creation of custom games by randomizing teams (with optional skill balancing), randomizing player roles, and randomizing champion bans based on the participants' primary champions. The UI will be built using Streamlit.

\#\# 2\. Core Technologies

\* \*\*Language:\*\* Python  
\* \*\*UI Framework:\*\* Streamlit  
\* \*\*Database:\*\* SQLite (via Python's \`sqlite3\` module)  
\* \*\*Champion Data:\*\* A local CSV file (\`champions.csv\`) containing a list of all League of Legends champion names.

\#\# 3\. Database Schema

A single SQLite database file (e.g., \`lol\_custom\_organizer.db\`) will be used.

\*\*Table: \`players\`\*\*

| Column Name        | Data Type     | Constraints              | Description                                      |  
| \------------------ | \------------- | \------------------------ | \------------------------------------------------ |  
| \`id\`               | INTEGER       | PRIMARY KEY AUTOINCREMENT | Unique identifier for the player.                |  
| \`name\`             | TEXT          | NOT NULL, UNIQUE         | Player's in-game name or nickname.               |  
| \`rank\`             | TEXT          | NOT NULL                 | Player's current LoL rank (e.g., "Gold", "Diamond"). |  
| \`primary\_champion\_1\`| TEXT          |                          | Player's first primary champion.                 |  
| \`primary\_champion\_2\`| TEXT          |                          | Player's second primary champion.                |  
| \`primary\_champion\_3\`| TEXT          |                          | (Optional) Player's third primary champion.      |  
| \`notes\`            | TEXT          |                          | Any additional notes about the player.           |

\*\*Champion Ranks (for skill balancing \- conceptual mapping, can be adjusted):\*\*  
\* Iron: 1  
\* Bronze: 2  
\* Silver: 3  
\* Gold: 4  
\* Platinum: 5  
\* Emerald: 6  
\* Diamond: 7  
\* Master: 8  
\* Grandmaster: 9  
\* Challenger: 10  
\*(The application should have a configurable mapping for these ranks to numerical values).\*

\#\# 4\. Champion Data File (\`champions.csv\`)

A CSV file named \`champions.csv\` should be present in the application's root directory.  
\*\*Format:\*\*  
\`\`\`csv  
ChampionName  
Aatrox  
Ahri  
Akali  
... (list all champions)

This file will be used for populating dropdowns for champion selection and for the random ban process if needed.

## **5\. Application Structure (Streamlit Pages)**

The application will have two main pages:

### **5.1. Page 1: Player Management (player\_management.py)**

**Purpose:** Allows users to add, view, edit, and delete players from the database.

**UI Elements & Functionality:**

* **Title:** "Player Management"  
* **Add New Player Section:**  
  * Input field for "Player Name" (Text Input).  
  * Dropdown for "Rank" (Selectbox, populated with standard LoL ranks).  
  * Dropdown/Multiselect for "Primary Champion 1" (Selectbox, populated from champions.csv).  
  * Dropdown/Multiselect for "Primary Champion 2" (Selectbox, populated from champions.csv).  
  * Dropdown/Multiselect for "Primary Champion 3" (Optional, Selectbox, populated from champions.csv).  
  * Text area for "Notes" (Optional).  
  * Button: "Add Player".  
    * **Logic:** Validates input (name and rank are required). Checks for duplicate player names. Inserts the new player into the players table. Displays a success or error message.  
* **View/Modify Players Section:**  
  * **Title:** "Current Player List"  
  * A table (e.g., using st.dataframe or st.data\_editor) displaying all players from the database with columns: Name, Rank, Primary Champion 1, Primary Champion 2, Primary Champion 3, Notes.  
  * **Edit Functionality:**  
    * The st.data\_editor can be used to allow direct editing in the table. Changes should be saved back to the database.  
    * Alternatively, a "Select Player to Edit" dropdown and separate "Edit Form" (similar to Add Player form, pre-filled) can be implemented.  
  * **Delete Functionality:**  
    * A button or icon next to each player (or a selection mechanism \+ "Delete Selected Player" button).  
    * Confirmation dialog before deleting.  
    * **Logic:** Removes the selected player from the players table. Displays a success or error message.

### **5.2. Page 2: Draft Creator (draft\_creator.py)**

**Purpose:** Allows users to select players for a game, randomize teams, assign roles, and generate bans.

**UI Elements & Functionality:**

* **Title:** "Custom Game Draft Creator"  
* **Configuration Settings (Sidebar or Top Section):**  
  * Numeric Input: "Number of Bans to Select from Pool" (Default: 10, Min: 0, Max: 20 or more, based on pool size).  
  * Checkbox: "Attempt Skill Balancing for Teams" (Default: True).  
  * Numeric Input: "Max Team Rerolls Allowed" (Default: 2).  
  * Numeric Input: "Max Role Rerolls Per Team" (Default: 2).  
  * (Optional) Numeric Input: "Number of Additional Random Bans (from all champions)" (Default: 0).  
* **Step 1: Select Players (10 players for a standard 5v5)**  
  * Multiselect widget: "Select Participating Players" (populated with names from the players table). Must enforce selection of exactly 10 players.  
  * Button: "Lock Players & Proceed to Team Randomization".  
    * **Logic:** Stores the selected 10 players in session state. Disables player selection. Enables next step.  
* **Step 2: Team Randomization**  
  * Display Area: "Teams" (initially empty).  
  * Button: "Randomize Teams" (enabled after players are locked).  
    * **Logic:**  
      1. Retrieves selected players and their ranks.  
      2. If "Attempt Skill Balancing" is checked:  
         * Convert ranks to numerical values.  
         * Algorithm to distribute players into two teams (Team A, Team B) such that the sum of rank values on each team is as close as possible. (e.g., sort players by rank, then distribute one by one to the team with the lower current sum, or use a more sophisticated partitioning algorithm).  
      3. If "Attempt Skill Balancing" is unchecked: Purely random assignment to two teams of 5\.  
      4. Displays the two teams with player names.  
      5. Stores teams in session state.  
      6. Initializes remaining team rerolls count.  
  * Display: "Team Rerolls Remaining: X"  
  * Button: "Reroll Teams" (enabled if rerolls \> 0 and teams are formed).  
    * **Logic:** Decrements reroll count. Re-runs the team randomization logic. Updates display.  
* **Step 3: Role Assignment**  
  * Display Area: "Assigned Roles" (initially empty, shown after teams are set).  
  * Button: "Randomize Roles" (enabled after teams are finalized or after a team reroll).  
    * **Logic:**  
      1. For each team, define the 5 roles: Top, Jungle, Mid, ADC, Support.  
      2. Randomly assign one role to each player within their team, ensuring each role is filled once per team.  
      3. Displays players with their assigned teams and roles.  
      4. Stores roles in session state.  
      5. Initializes remaining role rerolls count for each team.  
  * Display: "Team A Role Rerolls Remaining: Y", "Team B Role Rerolls Remaining: Z"  
  * Button: "Team A: Reroll Roles" (enabled if rerolls \> 0 for Team A).  
    * **Logic:** Decrements Team A's role reroll count. Re-randomizes roles for Team A players only. Updates display.  
  * Button: "Team B: Reroll Roles" (enabled if rerolls \> 0 for Team B).  
    * **Logic:** Decrements Team B's role reroll count. Re-randomizes roles for Team B players only. Updates display.  
* **Step 4: Ban Phase**  
  * Display Area: "Banned Champions" (initially empty).  
  * Button: "Generate Bans" (enabled after roles are finalized or after role rerolls).  
    * **Logic:**  
      1. **Collect Primary Champions:** Get primary\_champion\_1 and primary\_champion\_2 (and primary\_champion\_3 if exists) for all 10 participating players. This forms the "Potential Ban List". Remove any duplicates and empty/None entries.  
      2. **Select from Pool:** Randomly select N champions from this "Potential Ban List" to be banned, where N is the "Number of Bans to Select from Pool" configured by the user. If the pool size is less than N, ban all champions in the pool.  
      3. **(Optional) Add Fully Random Bans:** If "Number of Additional Random Bans" \> 0, randomly select that many unique champions from the global champions.csv list that are not already in the ban list from step 2\.  
      4. Displays the final list of banned champions.  
      5. Stores bans in session state.  
* **Reset Button:**  
  * Button: "Start New Draft".  
    * **Logic:** Clears all session state related to the current draft (selected players, teams, roles, bans). Resets UI to Step 1\.

## **6\. Core Logic Details**

### **6.1. Database Interaction**

* Functions to add, retrieve, update, and delete players from the SQLite database.  
* Functions to fetch all player names for dropdowns.  
* Functions to fetch all champion names from champions.csv.

### **6.2. Skill Balancing Algorithm (Example)**

1. Get list of 10 selected players with their numerical ranks.  
2. Sort players by rank in descending order.  
3. Initialize Team A and Team B sums to 0\.  
4. Iterate through sorted players:  
   * If Team A sum \<= Team B sum, add player to Team A and update Team A sum.  
   * Else, add player to Team B and update Team B sum.  
5. This is a greedy approach. More complex algorithms (e.g., trying multiple permutations or simulated annealing) could be used but might be overkill. The greedy approach should provide reasonable balance.  
   * An alternative: Randomly shuffle players. Then iterate through pairs, swapping if it improves balance, for a few iterations.

### **6.3. State Management**

* Streamlit's st.session\_state will be crucial for maintaining the state of the draft across interactions (selected players, formed teams, assigned roles, bans, remaining rerolls, etc.).

## **7\. Error Handling and User Feedback**

* Use st.success(), st.error(), st.warning(), st.info() to provide feedback to the user after operations.  
* Validate inputs (e.g., ensure 10 players are selected, player name is not empty).  
* Handle potential database errors gracefully.  
* Handle cases where champions.csv might be missing.

## **8\. Future Enhancements (Optional \- Not for initial build unless specified)**

* **Role Preferences:** Allow players to specify preferred/off-roles, and the role randomizer tries to accommodate them.  
* **Champion Draft Pick/Ban Phase Emulation:** A more interactive pick/ban phase instead of just generating bans.  
* **Saving/Loading Draft Configurations:** Save settings for number of bans, rerolls, etc.  
* **Game History:** Store past game results (teams, bans, winner).  
* **API for Champion List:** Fetch champion list dynamically from an API (e.g