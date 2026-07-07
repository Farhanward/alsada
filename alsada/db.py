"""SQLite persistence for probes (enables trend over time)."""
import json
import sqlite3

from alsada.config import DATA_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, ts REAL, engine TEXT, model TEXT, n_prompts INTEGER
);
CREATE TABLE IF NOT EXISTS probes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT, ts REAL, engine TEXT, model TEXT,
  prompt_id TEXT, prompt_text TEXT, lang TEXT, topic TEXT, answer TEXT,
  mentioned INTEGER, mention_count INTEGER, prominence REAL,
  client_cited INTEGER, sentiment TEXT,
  competitors TEXT, citations TEXT, flags TEXT
);
"""


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATA_DIR / "alsada.db"))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_run(conn, run_id, ts, engine, model, n_prompts):
    conn.execute(
        "INSERT OR REPLACE INTO runs(run_id, ts, engine, model, n_prompts) VALUES (?,?,?,?,?)",
        (run_id, ts, engine, model, n_prompts),
    )
    conn.commit()


def insert_probe(conn, run_id, ts, engine, model, prompt, answer, an):
    conn.execute(
        """INSERT INTO probes(run_id, ts, engine, model, prompt_id, prompt_text, lang, topic,
            answer, mentioned, mention_count, prominence, client_cited, sentiment,
            competitors, citations, flags)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, ts, engine, model, prompt.get("id"), prompt.get("text"),
         prompt.get("lang"), prompt.get("topic"), answer,
         1 if an["mentioned"] else 0, an["mention_count"], an["prominence"],
         1 if an["client_cited"] else 0, an["sentiment"],
         json.dumps(an["competitors"], ensure_ascii=False),
         json.dumps(an["citations"], ensure_ascii=False),
         json.dumps(an["flags"], ensure_ascii=False)),
    )
    conn.commit()


def latest_run_id(conn):
    row = conn.execute("SELECT run_id FROM runs ORDER BY ts DESC LIMIT 1").fetchone()
    return row["run_id"] if row else None


def read_probes(conn, run_id):
    rows = conn.execute("SELECT * FROM probes WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
    out = []
    for r in rows:
        out.append({
            "prompt_id": r["prompt_id"], "prompt_text": r["prompt_text"],
            "lang": r["lang"], "topic": r["topic"], "engine": r["engine"],
            "answer": r["answer"],
            "mentioned": bool(r["mentioned"]), "mention_count": r["mention_count"],
            "prominence": r["prominence"], "client_cited": bool(r["client_cited"]),
            "sentiment": r["sentiment"],
            "competitors": json.loads(r["competitors"] or "[]"),
            "citations": json.loads(r["citations"] or "[]"),
            "flags": json.loads(r["flags"] or "[]"),
        })
    return out
