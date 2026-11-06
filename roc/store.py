"""Versioned, transactional SQLite snapshots plus durable game-event history.

One GameService controls a save. Revision checking detects accidental concurrent
service instances instead of silently overwriting the second writer's progress.
The state is serialized as JSON to keep the schema resilient as game rules grow.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class SaveConflictError(RuntimeError):
    """A different game process/service changed the save after it was loaded."""


class SQLiteStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY CHECK(id=1),
                version INTEGER NOT NULL,
                data TEXT NOT NULL)''')
            columns = {row[1] for row in db.execute('PRAGMA table_info(snapshots)')}
            if 'revision' not in columns:
                db.execute('ALTER TABLE snapshots ADD COLUMN revision INTEGER NOT NULL DEFAULT 0')
            db.execute('''CREATE TABLE IF NOT EXISTS event_log (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, time REAL, event TEXT, detail TEXT)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute('PRAGMA busy_timeout=15000')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def load_with_revision(self):
        with self.connect() as db:
            row = db.execute('SELECT data, revision FROM snapshots WHERE id=1').fetchone()
        if not row:
            return None, 0
        return json.loads(row[0]), int(row[1])

    def load(self):
        return self.load_with_revision()[0]

    def commit(self, state, events=(), expected_revision=None):
        serialized = json.dumps(state, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT revision FROM snapshots WHERE id=1').fetchone()
            old_revision = int(row[0]) if row else 0
            if expected_revision is not None and old_revision != expected_revision:
                raise SaveConflictError(
                    f'stale game save (loaded revision {expected_revision}, current {old_revision})')
            new_revision = old_revision + 1
            if row:
                db.execute('UPDATE snapshots SET version=?, revision=?, data=? WHERE id=1',
                           (state.get('schema', 1), new_revision, serialized))
            else:
                db.execute('INSERT INTO snapshots(id,version,revision,data) VALUES(1,?,?,?)',
                           (state.get('schema', 1), new_revision, serialized))
            for ev in events:
                db.execute('INSERT INTO event_log(time,event,detail) VALUES(?,?,?)',
                           (ev.get('time'), ev.get('type'),
                            json.dumps(ev, ensure_ascii=False, allow_nan=False)))
        return new_revision

    def reset(self,state,expected_revision):
        """Start a truly fresh save and clear prior event history atomically."""
        serialized=json.dumps(state,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT revision FROM snapshots WHERE id=1').fetchone()
            old_revision=int(row[0]) if row else 0
            if old_revision!=expected_revision:
                raise SaveConflictError('save changed before new-game reset')
            new_revision=old_revision+1
            db.execute('INSERT INTO snapshots(id,version,revision,data) VALUES(1,?,?,?) '
                       'ON CONFLICT(id) DO UPDATE SET version=excluded.version, '
                       'revision=excluded.revision,data=excluded.data',
                       (state.get('schema',2),new_revision,serialized))
            db.execute('DELETE FROM event_log')
        return new_revision

    def recent_events(self, limit=50):
        if type(limit) is not int or limit<1:
            raise ValueError('limit must be a positive integer')
        with self.connect() as db:
            rows = db.execute('SELECT detail FROM event_log ORDER BY seq DESC LIMIT ?',
                              (min(5000,limit),)).fetchall()
        return [json.loads(row[0]) for row in rows]
