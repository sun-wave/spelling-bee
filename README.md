# NYT Spelling Bee Discord Bot

This is a Discord bot that allows users to play the New York Times Spelling Bee game directly within Discord channels. It fetches daily puzzles, tracks guesses, provides hints, and keeps score.

## Features

*   **Start Game (`;sb <date>`):** Start a new Spelling Bee game. If no date is provided, it defaults to today's puzzle. You can specify a date in `YYYY-MM-DD` format (e.g., `;sb 2026-03-29`).
*   **Guessing:** Once a game is active, any single word message sent in the channel (not starting with the command prefix) will be treated as a guess.
*   **End Game (`;sbend`):** Ends the current Spelling Bee game in the channel and displays the final scores.
*   **Hints (`;sbhint`):** Provides hints for the active game, including a letter/length grid and two-letter combinations of remaining words.
*   **Found Words (`;ans`):** Displays all words that have been found so far in the current game.

## Setup Instructions

### 1. Prerequisites

*   Python 3.8+
*   A Discord Bot Token (create one on the [Discord Developer Portal](https://discord.com/developers/applications))

### 2. Installation

1.  **Clone the repository (or download the files):**
    ```bash
    git clone <repository-url>
    cd spelling-bee
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  **Create a `.env` file:**
    In the root directory of the project, create a file named `.env`.

2.  **Add your Discord Bot Token:**
    Open the `.env` file and add your bot token as follows, replacing `YOUR_BOT_TOKEN_HERE` with your actual token:
    ```
    DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
    ```
    _You can refer to `.env.example` for the expected format._

### 4. Running the Bot

**Run the `main.py` script:**
```bash
python main.py
```

The bot should now be online in your Discord server.

## Usage

Invite your bot to a Discord server and use the following commands:

*   `;sb` - Start a new Spelling Bee game for today's puzzle.
*   `;sb 2026-03-29` - Start a Spelling Bee game for a specific date.
*   `;sbhint` - Get hints for the current active game.
*   `;ans` - See the words that have already been found.
*   `;sbend` - End the current game and see the final scores.

Happy puzzling!
