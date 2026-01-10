import tkinter as tk
from tkinter import ttk, messagebox
import json
import oracledb

# Importujeme naše repozitáře
# (Předpokládáme, že se to spouští z rootu, takže cesty src.XXX budou fungovat)
from src.Core.Database import Database
from src.Repository.MaterialRepository import MaterialRepository
from src.Repository.OrderRepository import OrderRepository
from src.Repository.ClientRepository import ClientRepository

class ToxicManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # 1. Základní nastavení okna
        self.title("☢️ TOXIC MANAGER v2.0 (GUI)")
        self.geometry("900x650")
        
        # 2. Připojení k databázi
        try:
            self.db = Database()
            self.connection = self.db.connect()
            self.repo_material = MaterialRepository(self.connection)
            self.repo_order = OrderRepository(self.connection)
            self.repo_client = ClientRepository(self.connection)
        except Exception as e:
            messagebox.showerror("Chyba připojení", f"Nelze se připojit k DB:\n{e}")
            self.destroy()
            return

        # 3. Vytvoření systému záložek (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- ZÁLOŽKA 1: SKLAD (Materiály) ---
        self.tab_materials = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_materials, text="📦 Sklad & Materiály")
        self.setup_materials_tab()

        # --- ZÁLOŽKA 2: NOVÁ OBJEDNÁVKA ---
        self.tab_order = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_order, text="📝 Nová Objednávka")
        self.setup_order_tab()

        # --- ZÁLOŽKA 3: REPORTY ---
        self.tab_report = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="💰 Finanční Report")
        self.setup_report_tab()

        # --- ZÁLOŽKA 4: ADMIN / IMPORT ---
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text="⚙️ Admin & Import")
        self.setup_admin_tab()

        # Načíst data do tabulek při startu
        self.refresh_materials()
        self.refresh_report()

    # ==========================================
    # LOGIKA ZÁLOŽKY 1: SKLAD (CRUD)
    # ==========================================
    def setup_materials_tab(self):
        # A: PŘIDÁNÍ
        frame_add = ttk.LabelFrame(self.tab_materials, text="➕ Přidat nový materiál")
        frame_add.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_add, text="Název:").pack(side="left", padx=5)
        self.entry_add_name = ttk.Entry(frame_add, width=20)
        self.entry_add_name.pack(side="left", padx=5)

        ttk.Label(frame_add, text="Cena (Kč):").pack(side="left", padx=5)
        self.entry_add_price = ttk.Entry(frame_add, width=10)
        self.entry_add_price.pack(side="left", padx=5)

        ttk.Label(frame_add, text="Nebezpečnost:").pack(side="left", padx=5)
        self.combo_add_hazard = ttk.Combobox(frame_add, values=["Low", "Medium", "High", "Death"], width=10)
        self.combo_add_hazard.pack(side="left", padx=5)
        self.combo_add_hazard.current(0)

        ttk.Button(frame_add, text="Uložit", command=self.add_material_action).pack(side="left", padx=20)

        # B: TABULKA
        self.tree_materials = ttk.Treeview(self.tab_materials, columns=("id", "name", "price", "hazard", "active"), show="headings", height=10)
        
        self.tree_materials.heading("id", text="ID")
        self.tree_materials.heading("name", text="Název")
        self.tree_materials.heading("price", text="Cena (Kč/kg)")
        self.tree_materials.heading("hazard", text="Nebezpečnost")
        self.tree_materials.heading("active", text="Stav")
        
        self.tree_materials.column("id", width=50)
        self.tree_materials.pack(expand=True, fill="both", padx=10, pady=5)
        self.tree_materials.bind("<<TreeviewSelect>>", self.on_material_select)

       # --- ČÁST C: ÚPRAVA A MAZÁNÍ (UPDATE & DELETE) ---
        frame_action = ttk.LabelFrame(self.tab_materials, text="✏️ Úprava vybraného")
        frame_action.pack(fill="x", padx=10, pady=5)

        # ID (jen pro čtení)
        ttk.Label(frame_action, text="ID:").pack(side="left", padx=5)
        self.entry_edit_id = ttk.Entry(frame_action, width=5, state="readonly")
        self.entry_edit_id.pack(side="left", padx=5)

        # Cena
        ttk.Label(frame_action, text="Cena:").pack(side="left", padx=5)
        self.entry_edit_price = ttk.Entry(frame_action, width=10)
        self.entry_edit_price.pack(side="left", padx=5)

        # NOVÉ: Nebezpečnost (Combobox)
        ttk.Label(frame_action, text="Hazard:").pack(side="left", padx=5)
        self.combo_edit_hazard = ttk.Combobox(frame_action, values=["Low", "Medium", "High", "Death"], width=10)
        self.combo_edit_hazard.pack(side="left", padx=5)

        # Tlačítka
        # Pozor: změnil se název funkce na 'update_material_action'
        ttk.Button(frame_action, text="💾 Uložit změny", command=self.update_material_action).pack(side="left", padx=10)
        ttk.Button(frame_action, text="🗑️ Smazat", command=self.delete_material_action).pack(side="right", padx=10)
        ttk.Button(frame_action, text="♻️ Obnovit", command=self.restore_material_action).pack(side="right", padx=5)
        ttk.Button(frame_action, text="🔄 Obnovit tabulku", command=self.refresh_materials).pack(side="right", padx=5)

    def add_material_action(self):
        name = self.entry_add_name.get()
        price_text = self.entry_add_price.get()
        hazard = self.combo_add_hazard.get()
        if not name or not price_text:
            return
        try:
            price = float(price_text)
            if self.repo_material.add(name, price, hazard):
                messagebox.showinfo("Úspěch", f"Materiál '{name}' přidán.")
                self.refresh_materials()
                self.entry_add_name.delete(0, 'end')
                self.entry_add_price.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Chyba", "Cena musí být číslo!")

    def on_material_select(self, event):
        selected_item = self.tree_materials.selection()
        if selected_item:
            values = self.tree_materials.item(selected_item)['values']
            # values = (id, name, price, hazard, active)
            
            # 1. Vyplnit ID
            self.entry_edit_id.config(state="normal")
            self.entry_edit_id.delete(0, 'end')
            self.entry_edit_id.insert(0, values[0])
            self.entry_edit_id.config(state="readonly")
            
            # 2. Vyplnit Cenu
            self.entry_edit_price.delete(0, 'end')
            self.entry_edit_price.insert(0, values[2])

            # 3. Vyplnit Hazard (NOVÉ)
            self.combo_edit_hazard.set(values[3])

    def refresh_materials(self):
        for item in self.tree_materials.get_children():
            self.tree_materials.delete(item)
        data = self.repo_material.get_all()
        for m in data:
            stav = "AKTIVNÍ" if m[4] == 1 else "NEAKTIVNÍ"
            self.tree_materials.insert("", "end", values=(m[0], m[1], m[2], m[3], stav))

    def update_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            price = float(self.entry_edit_price.get())
            hazard = self.combo_edit_hazard.get() # Načteme hodnotu z roletky
            
            if self.repo_material.update_material(mat_id, price, hazard):
                messagebox.showinfo("Úspěch", "Materiál byl aktualizován.")
                self.refresh_materials()
                # Volitelné: vymazat políčka po uložení
                self.entry_edit_price.delete(0, 'end')
                self.combo_edit_hazard.set('')
            else:
                messagebox.showerror("Chyba", "Aktualizace se nezdařila.")
        except ValueError:
            messagebox.showwarning("Chyba", "Musíš vybrat řádek a zadat platnou cenu.")

    def delete_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            if messagebox.askyesno("Potvrdit", "Opravdu smazat?"):
                if self.repo_material.delete_material(mat_id):
                    self.refresh_materials()
        except ValueError:
            pass

    def restore_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            # Kontrola, jestli už není aktivní (volitelné, ale hezké)
            selected = self.tree_materials.selection()
            if selected:
                values = self.tree_materials.item(selected)['values']
                if values[4] == "AKTIVNÍ":
                    messagebox.showinfo("Info", "Tento materiál už je aktivní.")
                    return

            if messagebox.askyesno("Potvrdit", f"Opravdu obnovit materiál ID {mat_id}?"):
                if self.repo_material.restore_material(mat_id):
                    messagebox.showinfo("Hotovo", "Materiál je znovu aktivní!")
                    self.refresh_materials()
        except ValueError:
            messagebox.showwarning("Chyba", "Vyber neaktivní materiál v tabulce.")

    # ==========================================
    # LOGIKA ZÁLOŽKY 2: OBJEDNÁVKA
    # ==========================================
    def setup_order_tab(self):
        frame = ttk.Frame(self.tab_order)
        frame.pack(padx=20, pady=20)

        ttk.Label(frame, text="Vytvoření nové objednávky", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="ID Klienta:").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_order_client = ttk.Entry(frame)
        self.entry_order_client.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="ID Materiálu:").grid(row=2, column=0, sticky="e", pady=5)
        self.entry_order_mat = ttk.Entry(frame)
        self.entry_order_mat.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Množství (kg):").grid(row=3, column=0, sticky="e", pady=5)
        self.entry_order_qty = ttk.Entry(frame)
        self.entry_order_qty.grid(row=3, column=1, pady=5)

        ttk.Button(frame, text="🚀 Odeslat", command=self.create_order_action).grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")

    def create_order_action(self):
        try:
            client = int(self.entry_order_client.get())
            mat = int(self.entry_order_mat.get())
            qty = float(self.entry_order_qty.get())
            
            kosik = [{'material_id': mat, 'quantity': qty}]
            order_id = self.repo_order.create_order(client, kosik)
            
            if order_id:
                messagebox.showinfo("Úspěch", f"Objednávka č. {order_id} vytvořena!")
                self.refresh_report()
            else:
                messagebox.showerror("Chyba", "Transakce selhala.")
        except ValueError:
            messagebox.showerror("Chyba", "Zkontroluj čísla.")

    # ==========================================
    # LOGIKA ZÁLOŽKY 3: REPORT
    # ==========================================
    def setup_report_tab(self):
        ttk.Button(self.tab_report, text="🔄 Aktualizovat", command=self.refresh_report).pack(pady=5)
        columns = ("firma", "pocet", "celkem")
        self.tree_report = ttk.Treeview(self.tab_report, columns=columns, show="headings")
        self.tree_report.heading("firma", text="Firma")
        self.tree_report.heading("pocet", text="Objednávek")
        self.tree_report.heading("celkem", text="Celkem")
        self.tree_report.pack(expand=True, fill="both", padx=10, pady=5)

    def refresh_report(self):
        for item in self.tree_report.get_children():
            self.tree_report.delete(item)
        try:
            data = self.repo_order.get_report()
            for row in data:
                self.tree_report.insert("", "end", values=(row[0], row[1], f"{row[2]:,.2f} Kč"))
        except: pass

    # ==========================================
    # LOGIKA ZÁLOŽKY 4: ADMIN
    # ==========================================
    def setup_admin_tab(self):
        frame = ttk.Frame(self.tab_admin)
        frame.pack(padx=20, pady=20)
        ttk.Label(frame, text="Import dat ze souboru JSON", font=("Arial", 12)).pack(pady=10)
        ttk.Button(frame, text="📥 Spustit Import", command=self.run_import).pack(pady=10)

    def run_import(self):
        try:
            with open('import_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                count_c, count_m = 0, 0
                for c in data.get('clients', []):
                    self.repo_client.add(c['name'], c['email'], c['credit'])
                    count_c += 1
                for m in data.get('materials', []):
                    self.repo_material.add(m['name'], m['price'], m['hazard'])
                    count_m += 1
                messagebox.showinfo("Import", f"Hotovo!\nKlientů: {count_c}\nMateriálů: {count_m}")
                self.refresh_materials()
        except Exception as e:
            messagebox.showerror("Chyba", f"{e}")

    def on_closing(self):
        if self.connection:
            self.connection.close()
        self.destroy()