import oracledb
# Importujeme model
from src.Model.Order import Order

class OrderRepository:
    def __init__(self, connection):
        self.connection = connection

    def create_order(self, client_id, cart):
        """ Vytvoří objednávku (Transakce) + Aplikuje VIP slevu """
        cursor = self.connection.cursor()
        try:
            # 1. Zjistit kredit a VIP status klienta
            # POZOR: Předpokládám, že sloupec se jmenuje 'credit'. 
            # Pokud máš v DB 'credit_balance', přepiš to v SQL níže.
            cursor.execute("SELECT credit, is_vip FROM clients WHERE id = :1", [client_id])
            client_row = cursor.fetchone()

            if not client_row:
                print("Klient neexistuje.")
                return None

            current_credit = client_row[0]
            is_vip = client_row[1] # 1 = VIP, 0 = Standard

            # 2. Spočítat celkovou cenu (s případnou slevou)
            total_price = 0
            prepared_items = [] # Sem si uložíme vypočítané ceny, abychom je pak vložili

            for item in cart:
                cursor.execute("SELECT price_per_kg FROM materials WHERE id = :1", [item['material_id']])
                res = cursor.fetchone()
                if not res:
                    print(f"Chyba: Materiál ID {item['material_id']} neexistuje")
                    return None
                
                base_price_per_kg = res[0]
                
                # --- APLIKACE SLEVY PRO VIP ---
                if is_vip == 1:
                    # VIP má 10% slevu na cenu za kg
                    final_price_per_kg = base_price_per_kg * 0.9
                else:
                    final_price_per_kg = base_price_per_kg
                
                # Cena za tuto položku (množství * zlevněná cena)
                item_total_price = final_price_per_kg * item['quantity']
                total_price += item_total_price
                
                # Uložíme si to bokem pro pozdější INSERT
                prepared_items.append({
                    'material_id': item['material_id'],
                    'quantity': item['quantity'],
                    'final_price': item_total_price
                })

            # 3. Zkontrolovat kredit (až po slevě)
            if current_credit < total_price:
                print(f"Nedostatek kreditu! Má: {current_credit}, Potřebuje: {total_price}")
                return None

            # 4. Vytvořit objednávky (INSERT)
            last_created_id = None
            
            for item_data in prepared_items:
                # A) Vytvoříme si "krabičku" na nové ID předem (pro Oracle)
                out_id = cursor.var(int)

                sql_insert = """
                    INSERT INTO orders (client_id, material_id, quantity, total_price, created_at)
                    VALUES (:1, :2, :3, :4, CURRENT_DATE)
                    RETURNING id INTO :5
                """

                # B) Předáme parametry (včetně zlevněné ceny)
                cursor.execute(sql_insert, [
                    client_id, 
                    item_data['material_id'], 
                    item_data['quantity'], 
                    item_data['final_price'], 
                    out_id
                ])
                
                # C) Získáme ID
                last_created_id = out_id.getvalue()[0]

            # 5. Odečíst peníze klientovi (UPDATE)
            cursor.execute("UPDATE clients SET credit = credit - :1 WHERE id = :2", 
                           [total_price, client_id])

            # Všechno klaplo, potvrdíme změny
            self.connection.commit()
            
            if is_vip == 1:
                print(f"🌟 Aplikována VIP sleva! Ušetřeno: {(total_price / 0.9) - total_price:.2f} Kč")
                
            return last_created_id

        except oracledb.Error as e:
            self.connection.rollback()
            print(f"Chyba transakce: {e}")
            return None

    def get_all_detailed(self):
        """ Vrací všechny objednávky vč. jmen klientů (přes VIEW) """
        cursor = self.connection.cursor()
        
        # POUŽITÍ VIEW 1: Už žádné složité JOINy v Pythonu!
        sql = "SELECT * FROM v_order_details ORDER BY id DESC"
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Převedeme na seznam slovníků pro GUI
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "company_name": row[1],
                "material_name": row[2],
                "quantity": row[3],
                "total_price": row[4],
                "created_at": row[5]
            })
        return data    

    def get_report(self):
        """ Agregovaný report (zůstává jako tuples, protože to nejsou objekty Order) """
        cursor = self.connection.cursor()
        sql = """
            SELECT c.company_name, COUNT(o.id), SUM(o.total_price)
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            GROUP BY c.company_name
        """
        cursor.execute(sql)
        return cursor.fetchall()

    def delete_order(self, order_id):
        """ Smaže objednávku """
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE id = :1", [order_id])
            self.connection.commit()
            return True
        except oracledb.Error as e:
            print(f"Chyba při mazání objednávky: {e}")
            return False
    def get_summary_report(self):
        """ 
        SPLNĚNÍ POŽADAVKU: Report ze 3 tabulek s agregací (SUM, COUNT, MAX).
        Spojuje: Clients, Orders, Materials
        """
        cursor = self.connection.cursor()
        sql = """
            SELECT 
                c.company_name, 
                COUNT(o.id) as pocet_objednavek,
                SUM(o.total_price) as celkova_utrata,
                MAX(m.hazard_level) as max_nebezpecnost
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            JOIN materials m ON o.material_id = m.id
            GROUP BY c.company_name
            ORDER BY celkova_utrata DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()