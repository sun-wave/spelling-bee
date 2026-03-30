# Spelling Bee Discord Bot

## Features

*   **Start Game (`:sb <date>`):** Start a new Spelling Bee game. If no date is provided, it defaults to today's puzzle. You can specify a date in `YYYY-MM-DD` format (e.g., `;sb 2026-03-29`).
*   **Guessing:** Once a game is active, any single word message sent in the channel (not starting with the command prefix) will be treated as a guess.
*   **End Game (`:sbend`):** Ends the current Spelling Bee game in the channel and displays the final scores.
*   **Hints (`:sbhint`):** Provides hints for the active game, including a letter/length grid and two-letter combinations of remaining words.
*   **Found Words (`:ans`):** Displays all words that have been found so far in the current game.

## Usage

Invite your bot to a Discord server and use the following commands:

*   `;sb` - Start a new Spelling Bee game for today's puzzle.
*   `;sb 2026-03-29` - Start a Spelling Bee game for a specific date.
*   `;sbhint` - Get hints for the current active game.
*   `;ans` - See the words that have already been found.
*   `;sbend` - End the current game and see the final scores.

Happy puzzling!
