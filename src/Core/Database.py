import oracledb
import configparser
import os

class Database:
    def __init__(self):
        # Načteme konfiguraci hned při vytvoření objektu
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

    def connect(self):
        """
        Tato metoda se připojí k databázi a vrátí connection objekt.
        Volá se v main.py jako db.connect()
        """
        try:
            # Načteme údaje ze sekce [database]
            user = self.config['database']['user']
            password = self.config['database']['password']
            dsn = self.config['database']['dsn']

            # Vytvoříme spojení
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            return connection

        except KeyError as e:
            print(f"CHYBA KONFIGURACE: V config.ini chybí klíč {e}")
            raise # Pošleme chybu dál, ať ji chytí main.py
        except oracledb.Error as e:
            print(f"CHYBA ORACLE: {e}")
            raise
    
    _connection = None

    @staticmethod
    def get_connection():
        if Database._connection is not None:
            return Database._connection

        config = configparser.ConfigParser()
        # Hledáme config.ini v kořenové složce
        if not os.path.exists('config.ini'):
            raise Exception("CHYBA: Soubor config.ini nebyl nalezen!")
            
        config.read('config.ini')
        
        try:
            user = config['database']['user']
            password = config['database']['password']
            dsn = config['database']['dsn']
            
            Database._connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn
            )
            print("--- ÚSPĚŠNĚ PŘIPOJENO K ORACLE DB ---")
            return Database._connection
        except Exception as e:
            print(f"Chyba v Database.py: {e}")
            raise