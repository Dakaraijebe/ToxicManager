import oracledb

class Client:
    def __init__(self, id, name, email, credit):
        self.id = id
        self.name = name
        self.email = email
        self.credit = credit

class ClientRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        cursor = self.connection.cursor()
        # Už žádné is_vip
        cursor.execute("SELECT id, company_name, email, credit_balance FROM clients ORDER BY id")
        rows = cursor.fetchall()
        clients = []
        for row in rows:
            clients.append(Client(row[0], row[1], row[2], row[3]))
        return clients

    def add(self, name, email, credit):
        try:
            cursor = self.connection.cursor()
            sql = "INSERT INTO clients (company_name, email, credit_balance) VALUES (:1, :2, :3)"
            cursor.execute(sql, [name, email, credit])
            self.connection.commit()
            return True
        except oracledb.Error as e:
            print(f"Chyba DB: {e}")
            return False

    def update_client(self, client_id, name, email, credit):
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE clients SET company_name = :1, email = :2, credit_balance = :3 WHERE id = :4"
            cursor.execute(sql, [name, email, credit, client_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False

    def delete_client(self, client_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM clients WHERE id = :1", [client_id])
            self.connection.commit()
            return True, "Smazáno"
        except oracledb.Error as e:
            if "integrity constraint" in str(e).lower():
                return False, "Nelze smazat klienta, který má objednávky!"
            return False, str(e)