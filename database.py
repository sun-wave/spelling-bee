import aiosqlite
import json
from datetime import datetime

DB_NAME = "spelling_bee.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS server_configs (
                server_id INTEGER PRIMARY KEY,
                channel_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id TEXT PRIMARY KEY,
                channel_id INTEGER,
                server_id INTEGER,
                game_data TEXT,
                timestamp TEXT
            )
        """)
        await db.commit()

async def set_channel_config(server_id, channel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO server_configs (server_id, channel_id) VALUES (?, ?)",
            (server_id, channel_id)
        )
        await db.commit()

async def get_channel_config(server_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT channel_id FROM server_configs WHERE server_id = ?",
            (server_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_game_session(session_id, channel_id, server_id, game_data):
    async with aiosqlite.connect(DB_NAME) as db:
        timestamp = datetime.now().isoformat()
        await db.execute("""
            INSERT OR REPLACE INTO game_sessions (session_id, channel_id, server_id, game_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            channel_id,
            server_id,
            json.dumps(game_data), # Store game_data as JSON string
            timestamp
        ))
        await db.commit()

async def load_game_session(channel_id, server_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT game_data FROM game_sessions 
            WHERE channel_id = ? AND server_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (channel_id, server_id)) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

async def clear_game_sessions(channel_id, server_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM game_sessions WHERE channel_id = ? AND server_id = ?",
            (channel_id, server_id)
        )
        await db.commit()

async def load_all_active_sessions():
    async with aiosqlite.connect(DB_NAME) as db:
        # Subquery to get the latest session_id for each channel_id and server_id
        async with db.execute("""
            SELECT
                s1.session_id, s1.channel_id, s1.server_id, s1.game_data
            FROM
                game_sessions s1
            INNER JOIN (
                SELECT
                    channel_id, server_id, MAX(timestamp) as max_timestamp
                FROM
                    game_sessions
                GROUP BY
                    channel_id, server_id
            ) AS s2
            ON s1.channel_id = s2.channel_id AND s1.server_id = s2.server_id AND s1.timestamp = s2.max_timestamp
        """) as cursor:
            rows = await cursor.fetchall()
            sessions = []
            for row in rows:
                session_id, channel_id, server_id, game_data_json = row
                sessions.append({
                    "session_id": session_id,
                    "channel_id": channel_id,
                    "server_id": server_id,
                    "game_data": json.loads(game_data_json)
                })
            return sessions
