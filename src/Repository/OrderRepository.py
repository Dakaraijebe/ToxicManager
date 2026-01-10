import oracledb

class OrderRepository:
    def __init__(self, connection):
        self.connection = connection

    def create_order(self, client_id, items):
        """
        Vytvoří objednávku (Transakce).
        """
        cursor = self.connection.cursor()
        try:
            print(f"--- ZAHAJUJI TRANSAKCI PRO KLIENTA {client_id} ---")

            # 1. KROK: Vytvoření hlavičky objednávky
            new_id_var = cursor.var(oracledb.NUMBER)
            sql_order = """
                INSERT INTO orders (client_id, status)
                VALUES (:1, 'NEW')
                RETURNING id INTO :2
            """
            cursor.execute(sql_order, [client_id, new_id_var])
            new_order_id = new_id_var.getvalue()[0]
            print(f"  > Vytvořena objednávka s ID: {new_order_id}")

            # 2. KROK: Vložení položek
            sql_item = """
                INSERT INTO order_items (order_id, material_id, quantity)
                VALUES (:1, :2, :3)
            """
            for item in items:
                cursor.execute(sql_item, [new_order_id, item['material_id'], item['quantity']])
            
            # 3. KROK: Potvrzení transakce
            self.connection.commit()
            print("✅ TRANSAKCE ÚSPĚŠNÁ - Vše uloženo.")
            return new_order_id

        except Exception as e:
            self.connection.rollback()
            print(f"❌ CHYBA! Transakce selhala. Vracím změny zpět.")
            print(f"Detail chyby: {e}")
            return None

    def get_report(self):
        """
        Splňuje bod zadání: Agregovaný report ze 3+ tabulek.
        Spočítá celkovou útratu pro každého klienta.
        """
        cursor = self.connection.cursor()
        # Spojujeme 4 tabulky: Clients -> Orders -> OrderItems -> Materials
        sql = """
            SELECT 
                c.company_name, 
                COUNT(DISTINCT o.id) as pocet_objednavek,
                SUM(oi.quantity * m.price_per_kg) as celkova_utrata
            FROM clients c
            JOIN orders o ON c.id = o.client_id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN materials m ON oi.material_id = m.id
            GROUP BY c.company_name
            ORDER BY celkova_utrata DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()