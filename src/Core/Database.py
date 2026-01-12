import oracledb
import configparser
import os

class Database:
    def __init__(self):
        self.config = configparser.ConfigParser()
        
        # 1. Zjistíme cestu k tomuto souboru (src/Core/Database.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Vypočítáme cestu k rootu projektu (o 2 úrovně výš -> ToxicManager)
        # src/Core -> src -> ToxicManager
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # 3. Cesta ke config/config.ini
        config_path = os.path.join(project_root, 'config', 'config.ini')
        
        # 4. Načteme konfiguraci
        read_files = self.config.read(config_path)
        
        if not read_files:
            raise FileNotFoundError(f"Konfigurační soubor nebyl nalezen!\nOčekávaná cesta: {config_path}")

    def connect(self):
        try:
            # Python ConfigParser je case-sensitive (citlivý na velikost písmen)
            # Ujisti se, že v config.ini je [DATABASE] velkými písmeny
            user = self.config['DATABASE']['user']
            password = self.config['DATABASE']['password']
            dsn = self.config['DATABASE']['dsn']
            
            connection = oracledb.connect(user=user, password=password, dsn=dsn)
            return connection
        except KeyError as e:
            raise Exception(f"Chyba v config.ini: Chybí sekce nebo klíč {e}")
        except oracledb.Error as e:
            raise Exception(f"Chyba připojení k Oracle: {e}")