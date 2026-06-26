import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, db_path='state.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS seen_roles (
                        url TEXT PRIMARY KEY,
                        company TEXT,
                        title TEXT,
                        fit_score REAL,
                        status TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing State DB: {e}")

    def is_new_role(self, url: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM seen_roles WHERE url = ?', (url,))
                result = cursor.fetchone()
                return result is None
        except Exception as e:
            logger.error(f"Error checking state for url {url}: {e}")
            return True

    def mark_seen(self, url: str, company: str, title: str, fit_score: float, status: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO seen_roles (url, company, title, fit_score, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (url, company, title, fit_score, status))
                conn.commit()
                logger.info(f"Marked role as {status}: {title} at {company}")
        except Exception as e:
            logger.error(f"Error saving state for {url}: {e}")
