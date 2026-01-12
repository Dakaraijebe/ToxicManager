import oracledb
from src.Core.Database import Database

def inspect():
    print("🕵️ ZAHAJUJI INSPEKCI STRUKTURY DATABÁZE...\n")
    
    try:
        db = Database()
        connection = db.connect()
        cursor = connection.cursor()
        
        # 1. Seznam našich tabulek (všechny velkými písmeny)
        my_tables = ['CATEGORIES', 'CLIENTS', 'MATERIALS', 'ORDERS', 'APP_LOGS']
        
        for table in my_tables:
            print(f"TABULKA: {table}")
            print("-" * 40)
            
            # Dotaz na sloupce v dané tabulce
            sql = """
                SELECT column_name, data_type, data_length, nullable 
                FROM user_tab_columns 
                WHERE table_name = :1 
                ORDER BY column_id
            """
            cursor.execute(sql, [table])
            rows = cursor.fetchall()
            
            if not rows:
                print("   ❌ TABULKA NEEXISTUJE!")
            else:
                # Výpis sloupců
                print(f"{'SLOUPEC':<20} {'TYP':<15} {'NULL?':<10}")
                for row in rows:
                    col_name = row[0]
                    col_type = row[1]
                    # Přidáme délku pro VARCHAR2
                    if col_type == 'VARCHAR2':
                        col_type = f"VARCHAR2({row[2]})"
                    is_null = 'ANO' if row[3] == 'Y' else 'NE'
                    
                    print(f"{col_name:<20} {col_type:<15} {is_null:<10}")
            print("\n")

        # 2. Kontrola cizích klíčů (Vazby)
        print("KONTROLA VAZEB (FOREIGN KEYS):")
        sql_fk = """
            SELECT a.constraint_name, a.table_name, a.column_name, c_pk.table_name r_table_name
            FROM user_cons_columns a
            JOIN user_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
            JOIN user_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
            WHERE c.constraint_type = 'R'
            AND a.table_name IN ('ORDERS', 'MATERIALS')
        """
        cursor.execute(sql_fk)
        fks = cursor.fetchall()
        for fk in fks:
            print(f"   ✅ {fk[1]}.{fk[2]}  --> odkazuje na -->  {fk[3]}")

    except Exception as e:
        print(f"❌ Chyba: {e}")
    finally:
        try: connection.close()
        except: pass

if __name__ == "__main__":
    inspect()