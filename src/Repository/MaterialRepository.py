import oracledb

class Material:
    def __init__(self, id, name, price, hazard, is_active, category_name):
        self.id = id
        self.name = name
        self.price = price
        self.hazard = hazard
        self.is_active = is_active
        self.category_name = category_name # <--- NOVÉ

class MaterialRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_all(self):
        cursor = self.connection.cursor()
        # JOINUJEME tabulku CATEGORIES, abychom získali její název
        sql = """
            SELECT m.id, m.name, m.price_per_kg, m.hazard_level, m.is_active, c.name
            FROM materials m
            LEFT JOIN categories c ON m.category_id = c.id
            ORDER BY m.id
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        materials = []
        for row in rows:
            # row[5] je název kategorie z JOINu
            cat_name = row[5] if row[5] else "Nezařazeno"
            materials.append(Material(row[0], row[1], row[2], row[3], row[4], cat_name))
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
            
            # Automatické přiřazení kategorie podle hazardu (jednoduchá logika pro školu)
            cat_id = None
            if hazard == 'Low':
                cursor.execute("SELECT id FROM categories WHERE name LIKE 'Běžný%' FETCH FIRST 1 ROWS ONLY")
            elif hazard == 'Death':
                cursor.execute("SELECT id FROM categories WHERE name LIKE 'Extrémně%' FETCH FIRST 1 ROWS ONLY")
            else:
                cursor.execute("SELECT id FROM categories WHERE name LIKE 'Nebezpečný%' FETCH FIRST 1 ROWS ONLY")
            
            res = cursor.fetchone()
            if res: cat_id = res[0]

            sql = "INSERT INTO materials (name, price_per_kg, hazard_level, is_active, category_id) VALUES (:1, :2, :3, 1, :4)"
            cursor.execute(sql, [name, price, hazard, cat_id])
            self.connection.commit()
            return True
        except oracledb.Error as e:
            print(f"Chyba DB: {e}")
            return False

    def update_material(self, material_id, new_price, new_hazard):
        try:
            cursor = self.connection.cursor()
            # Při update hazardu bychom správně měli update i kategorii, ale pro jednoduchost měníme jen cenu/hazard
            sql = "UPDATE materials SET price_per_kg = :1, hazard_level = :2 WHERE id = :3"
            cursor.execute(sql, [new_price, new_hazard, material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False

    def delete_material(self, material_id):
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE materials SET is_active = 0 WHERE id = :1"
            cursor.execute(sql, [material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False

    def restore_material(self, material_id):
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE materials SET is_active = 1 WHERE id = :1"
            cursor.execute(sql, [material_id])
            self.connection.commit()
            return True
        except oracledb.Error:
            return False