-- Run this in Supabase SQL editor to create the schema

-- Players table (upserted each sync)
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    squad_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'playing',
    positions TEXT[] NOT NULL DEFAULT '{}',
    games_played INTEGER DEFAULT 0,
    average_points REAL DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    last3_avg REAL DEFAULT 0,
    last5_avg REAL DEFAULT 0,
    high_score INTEGER DEFAULT 0,
    low_score INTEGER DEFAULT 0,
    live_score INTEGER,
    last_round_score INTEGER,
    scores JSONB DEFAULT '{}',
    ownership JSONB DEFAULT '{}',
    round_price_change INTEGER DEFAULT 0,
    season_price_change INTEGER DEFAULT 0,
    prices JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game stats table (one row per player per game)
CREATE TABLE IF NOT EXISTS game_stats (
    player_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    opponent_squad_id INTEGER NOT NULL,
    venue_id INTEGER NOT NULL,
    kicks INTEGER DEFAULT 0,
    handballs INTEGER DEFAULT 0,
    marks INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    frees_for INTEGER DEFAULT 0,
    frees_against INTEGER DEFAULT 0,
    hitouts INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    behinds INTEGER DEFAULT 0,
    time_on_ground INTEGER DEFAULT 0,
    disposals INTEGER DEFAULT 0,
    inside50 INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    clangers INTEGER DEFAULT 0,
    contested_possessions INTEGER DEFAULT 0,
    uncontested_possessions INTEGER DEFAULT 0,
    contested_marks INTEGER DEFAULT 0,
    goal_assist INTEGER DEFAULT 0,
    fantasy_score INTEGER DEFAULT 0,
    PRIMARY KEY (player_id, game_id)
);

-- Index for PAA queries
CREATE INDEX IF NOT EXISTS idx_game_stats_opponent ON game_stats(opponent_squad_id, round_number);
CREATE INDEX IF NOT EXISTS idx_game_stats_player ON game_stats(player_id, round_number);

-- PAA stored function (called by store.py get_paa_by_team)
CREATE OR REPLACE FUNCTION get_paa_by_team(position_filter TEXT, num_rounds INTEGER)
RETURNS TABLE(opponent_squad_id INTEGER, avg_score REAL)
LANGUAGE sql
AS $$
    SELECT
        gs.opponent_squad_id,
        AVG(gs.fantasy_score)::REAL AS avg_score
    FROM game_stats gs
    JOIN players p ON p.id = gs.player_id
    WHERE
        position_filter = ANY(p.positions)
        AND gs.round_number > (
            SELECT MAX(round_number) FROM game_stats
        ) - num_rounds
    GROUP BY gs.opponent_squad_id
    ORDER BY avg_score DESC;
$$;

-- Rounds table (season fixture)
CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY,
    round_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    is_bye_round BOOLEAN DEFAULT FALSE,
    bye_squads INTEGER[] DEFAULT '{}',
    games JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Posts table (draft X posts awaiting approval)
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    post_type TEXT NOT NULL,  -- 'trade', 'captain', 'differential', 'news'
    round_number INTEGER,
    status TEXT DEFAULT 'draft',  -- 'draft', 'approved', 'posted', 'rejected'
    telegram_message_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ
);
