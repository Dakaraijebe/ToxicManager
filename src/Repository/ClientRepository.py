import oracledb

class ClientRepository:
    def __init__(self, connection):
        self.connection = connection

    def add(self, name, email, credit):
        cursor = self.connection.cursor()
        # Vkládáme klienta, datum podpisu smlouvy dáme dnešní (CURRENT_DATE)
        sql = """
            INSERT INTO clients (company_name, contact_email, contract_signed_date, credit_balance)
            VALUES (:1, :2, CURRENT_DATE, :3)
        """
        try:
            cursor.execute(sql, [name, email, credit])
            self.connection.commit() # Uložíme to hned
            print(f"  > Klient '{name}' vložen.")
        except oracledb.Error as e:
            print(f"  ❌ Chyba u klienta {name}: {e}")