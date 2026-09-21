import sqlite3
import logging
from datetime import datetime


class Database:
    """ handles all SQLite databases """
    # --------------constant--------------
    DB_FILE = 'defensive.db'
    NAME_LEN = 255
    ID_LEN = 16
    AES_LEN = 32
    PUBLIC_KEY_LEN = 160


    def __init__(self, db_path:str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """ initialize database and create tables if needed """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # create clients table
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS clients (
                        ID BLOB PRIMARY KEY CHECK(length(ID) == {self.ID_LEN}),
                        Name TEXT NOT NULL CHECK(length(Name) <= {self.NAME_LEN}),
                        PublicKey BLOB CHECK(length(PublicKey) <= {self.PUBLIC_KEY_LEN}),
                        LastSeen DATETIME,
                        AES BLOB CHECK(length(AES) == {self.AES_LEN})
                    )                
                ''')

                # create files table
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS files (
                        ID BLOB CHECK(length(ID) == {self.ID_LEN}),
                        Filename TEXT NOT NULL CHECK(length(Filename) <= {self.NAME_LEN}),
                        PathName TEXT NOT NULL CHECK(length(PathName) <= {self.NAME_LEN}),
                        Verified BOOLEAN,
                        FOREIGN KEY (ID) REFERENCES clients (ID)
                    )
                ''')
                conn.commit()
                logging.info(f"database created at {self.db_path}")
        except sqlite3.Error as e:
            logging.critical(f"error creating database: {e}")
            raise

    def client_exists(self, name:str) -> bool:
        """ checks if client withe given name exists """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM clients WHERE Name = ?", (name,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"Error checking if client {name} exists in database: {e}")
            raise

    def register_client(self, client_id: bytes, name:str):
        """ registers a new client into the database """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                last_seen = datetime.now().isoformat()

                cursor.execute(
                    "INSERT INTO clients (ID, Name, LastSeen) VALUES (?, ?, ?)",
                    (client_id, name, last_seen)
                )
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error registering client: {e}")
            raise

    def update_client_key(self, client_id: bytes,public_key: bytes, aes_key: bytes):
        """ updates client with public key and AES key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE clients SET PublicKey = ?, AES = ? WHERE ID = ?",
                    (public_key, aes_key, client_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error updating client key for ID {client_id}: {e}")
            raise

    def update_client_last_seen(self, client_id: bytes) -> bool:
        """ updates client with last seen date """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                current_time = datetime.now().isoformat()
                cursor.execute(
                    "UPDATE clients SET LastSeen = ? WHERE ID = ?",
                    (current_time, client_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error updating client last seen for ID {client_id}: {e}")
            raise

    def get_client_public_key(self, client_id: bytes) -> bytes | None:
        """ gets client public key for a given ID """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT PublicKey FROM clients WHERE ID = ?", (client_id,))
                row = cursor.fetchone()

                # return only if exist
                if row and row[0]:
                    return row[0]
                return None
        except sqlite3.Error as e:
            logging.error(f"Error getting client public key for ID {client_id}: {e}")
            return None

    def get_client_aes_key(self, client_id: bytes) -> bytes | None:
        """ gets client AES key for a given ID """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT AES FROM clients WHERE ID = ?", (client_id,))
                row = cursor.fetchone()

                if row and row[0]:
                    return row[0]
                return None
        except sqlite3.Error as e:
            logging.error(f"Error getting client AES key for ID {client_id}: {e}")
            return None

    def save_file(self, client_id: bytes, filename: str, pathname: str):
        """ saves file to database """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO files (ID, Filename, PathName, Verified) VALUES (?, ?, ?, ?)",
                    (client_id, filename, pathname, False)
                )
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error saving file to database: {e}")
            raise

    def update_file_verified(self, client_id: bytes, filename: str):
        """ updates file to verified by client """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE files SET Verified = ? WHERE ID = ? AND Filename = ?",
                    (True, client_id, filename)
                )
                conn.commit()
                # return is we find and change the line
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error updating file to verified status for file {filename}: {e}")
            raise
