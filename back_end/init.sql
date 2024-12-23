CREATE TABLE players
(
    player_id    INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username     TEXT UNIQUE                       NOT NULL,
    password     TEXT                              NOT NULL CHECK (LENGTH(password) >= 12),
    forfeits     INTEGER DEFAULT 0,
    wins         INTEGER DEFAULT 0,
    losses       INTEGER DEFAULT 0,
    played_games INTEGER DEFAULT 0,
    score        INTEGER DEFAULT 1000
);
