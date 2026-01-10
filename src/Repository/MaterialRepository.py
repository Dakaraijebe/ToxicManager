import oracledb

class MaterialRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        cursor = self.connection.cursor()
        # Vybereme vše, seřadíme podle ID
        cursor.execute("SELECT id, name, price_per_kg, hazard_level, is_active FROM materials ORDER BY id")
        return cursor.fetchall()

    def add(self, name, price, hazard):
        """ Vloží nový materiál (CREATE) """
        cursor = self.connection.cursor()
        sql = """
            INSERT INTO materials (name, price_per_kg, hazard_level, is_active)
            VALUES (:1, :2, :3, 1)
        """
        try:
            # POZOR: Pořadí v seznamu musí odpovídat pořadí v SQL (:1, :2, :3)
            # 1=name (text), 2=price (číslo), 3=hazard (text)
            cursor.execute(sql, [name, price, hazard])
            self.connection.commit()
            print(f"✅ Materiál '{name}' úspěšně vložen.")
            return True
        except oracledb.Error as e:
            print(f"❌ Chyba při vkládání: {e}")
            return False

    # Nahraď původní 'update_price' touto novou metodou:
    def update_material(self, material_id, new_price, new_hazard):
        """ Upraví cenu A nebezpečnost materiálu (UPDATE) """
        cursor = self.connection.cursor()
        # SQL příkaz nyní mění dva sloupce: price_per_kg a hazard_level
        sql = "UPDATE materials SET price_per_kg = :1, hazard_level = :2 WHERE id = :3"
        try:
            cursor.execute(sql, [new_price, new_hazard, material_id])
            self.connection.commit()
            print(f"✅ Materiál ID {material_id} aktualizován.")
            return True
        except oracledb.Error as e:
            print(f"❌ Chyba při update: {e}")
            return False

    def delete_material(self, material_id):
        """ Označí materiál jako smazaný (DELETE / Soft Delete) """
        cursor = self.connection.cursor()
        sql = "UPDATE materials SET is_active = 0 WHERE id = :1"
        try:
            cursor.execute(sql, [material_id])
            self.connection.commit()
            return True
        except oracledb.Error as e:
            print(f"❌ Chyba při mazání: {e}")
            return False

    def restore_material(self, material_id):
        """ Vrátí materiál zpět do hry (is_active = 1) """
        cursor = self.connection.cursor()
        sql = "UPDATE materials SET is_active = 1 WHERE id = :1"
        try:
            cursor.execute(sql, [material_id])
            self.connection.commit()
            print(f"✅ Materiál ID {material_id} byl obnoven.")
            return True
        except oracledb.Error as e:
            print(f"❌ Chyba při obnovení: {e}")
            return False