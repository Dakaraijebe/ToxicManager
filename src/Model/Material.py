import oracledb

class Material:
    def __init__(self, id, name, price, hazard, is_active):
        self.id = id
        self.name = name
        self.price = price
        self.hazard = hazard
        self.is_active = is_active # Zde je náš BOOL (1/0)

class MaterialRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name, price_per_kg, hazard_level, is_active FROM materials ORDER BY id")
        rows = cursor.fetchall()
        materials = []
        for row in rows:
            materials.append(Material(row[0], row[1], row[2], row[3], row[4]))
        return materials

    def get_active_materials(self):
        """ Pro combobox v objednávce (používá VIEW) """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name, price_per_kg FROM v_active_materials ORDER BY name")
        rows = cursor.fetchall()
        materials = []
        for row in rows:
            materials.append({"id": row[0], "name": row[1], "price_per_kg": row[2]})
        return materials

    def add(self, name, price, hazard):
        try:
            cursor = self.connection.cursor()
            # Defaultně vkládáme is_active = 1
            sql = "INSERT INTO materials (name, price_per_kg, hazard_level, is_active) VALUES (:1, :2, :3, 1)"
            cursor.execute(sql, [name, price, hazard])
            self.connection.commit()
            return True
        except oracledb.Error as e:
            print(f"Chyba DB: {e}")
            return False

    def update_material(self, material_id, new_price, new_hazard):
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE materials SET price_per_kg = :1, hazard_level = :2 WHERE id = :3"
            cursor.execute(sql, [new_price, new_hazard, material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False

    def delete_material(self, material_id):
        """ SOFT DELETE: Nastaví Boolean na 0 """
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE materials SET is_active = 0 WHERE id = :1"
            cursor.execute(sql, [material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False

    def restore_material(self, material_id):
        """ OBNOVENÍ: Nastaví Boolean na 1 """
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE materials SET is_active = 1 WHERE id = :1"
            cursor.execute(sql, [material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False