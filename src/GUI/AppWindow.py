import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import oracledb

from src.Core.Database import Database
from src.Repository.MaterialRepository import MaterialRepository
from src.Repository.OrderRepository import OrderRepository
from src.Repository.ClientRepository import ClientRepository

class ToxicManagerGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # 1. Základní nastavení okna
        self.title("☢️ TOXIC MANAGER v2.0 (Final Clean Edition)")
        self.geometry("1100x750") # Trochu jsem rozšířil okno kvůli novému sloupci
        
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

        # 3. Záložky
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_materials = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_materials, text="📦 Sklad & Kategorie")
        self.setup_materials_tab()

        self.tab_clients = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_clients, text="👥 Klienti")
        self.setup_clients_tab()

        self.tab_orders_list = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_orders_list, text="📋 Seznam Objednávek")
        self.setup_orders_list_tab()

        self.tab_order = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_order, text="📝 Nová Objednávka")
        self.setup_order_tab()

        self.tab_report = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_report, text="💰 Finanční Report")
        self.setup_report_tab()

        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text="⚙️ Admin & Import")
        self.setup_admin_tab()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Načíst data
        self.refresh_materials()
        self.refresh_clients()
        self.refresh_orders_list()
        self.refresh_report()

    # ==========================================
    # LOGIKA ZÁLOŽKY 1: SKLAD (S kategoriemi a Booleanem)
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

        # B: TABULKA - ZDE BYLA CHYBA, NYNÍ OPRAVENO (přidáno "category" do columns)
        self.tree_materials = ttk.Treeview(
            self.tab_materials, 
            columns=("id", "name", "price", "hazard", "category", "active"), 
            show="headings", 
            height=10
        )
        
        self.tree_materials.heading("id", text="ID")
        self.tree_materials.heading("name", text="Název")
        self.tree_materials.heading("price", text="Cena (Kč/kg)")
        self.tree_materials.heading("hazard", text="Nebezpečnost")
        self.tree_materials.heading("category", text="Kategorie") # <--- Nový sloupec
        self.tree_materials.heading("active", text="Aktivní?")
        
        self.tree_materials.column("id", width=40)
        self.tree_materials.column("active", width=80)
        self.tree_materials.column("category", width=120)
        
        self.tree_materials.pack(expand=True, fill="both", padx=10, pady=5)
        self.tree_materials.bind("<<TreeviewSelect>>", self.on_material_select)

        # C: ÚPRAVA A MAZÁNÍ
        frame_action = ttk.LabelFrame(self.tab_materials, text="✏️ Úprava vybraného")
        frame_action.pack(fill="x", padx=10, pady=5)

        self.entry_edit_id = ttk.Entry(frame_action, width=5, state="readonly")
        self.entry_edit_id.pack(side="left", padx=5)

        self.entry_edit_price = ttk.Entry(frame_action, width=10)
        self.entry_edit_price.pack(side="left", padx=5)

        self.combo_edit_hazard = ttk.Combobox(frame_action, values=["Low", "Medium", "High", "Death"], width=10)
        self.combo_edit_hazard.pack(side="left", padx=5)

        ttk.Button(frame_action, text="💾 Uložit změny", command=self.update_material_action).pack(side="left", padx=10)
        
        # Tlačítka pro změnu Boolean hodnoty
        ttk.Button(frame_action, text="🔴 Deaktivovat", command=self.delete_material_action).pack(side="right", padx=5)
        ttk.Button(frame_action, text="🟢 Aktivovat", command=self.restore_material_action).pack(side="right", padx=5)
        ttk.Button(frame_action, text="🔄 Refresh", command=self.refresh_materials).pack(side="right", padx=5)

    def refresh_materials(self):
        for item in self.tree_materials.get_children():
            self.tree_materials.delete(item)
        
        data = self.repo_material.get_all()
        for m in data:
            if m.is_active == 1:
                stav = "✅ ANO"
            else:
                stav = "❌ NE"
            
            # Vkládáme i m.category_name
            self.tree_materials.insert("", "end", values=(m.id, m.name, m.price, m.hazard, m.category_name, stav))

    def on_material_select(self, event):
        selected_item = self.tree_materials.selection()
        if selected_item:
            values = self.tree_materials.item(selected_item)['values']
            # Hodnoty jsou: [ID, Name, Price, Hazard, Category, Active]
            # Indexy:        0    1      2      3        4        5
            
            self.entry_edit_id.config(state="normal")
            self.entry_edit_id.delete(0, 'end')
            self.entry_edit_id.insert(0, values[0])
            self.entry_edit_id.config(state="readonly")
            
            self.entry_edit_price.delete(0, 'end')
            self.entry_edit_price.insert(0, values[2])
            self.combo_edit_hazard.set(values[3])

    def add_material_action(self):
        name = self.entry_add_name.get()
        price_text = self.entry_add_price.get()
        hazard = self.combo_add_hazard.get()
        if not name or not price_text: return
        try:
            price = float(price_text)
            # Kategorie se přiřadí automaticky v repozitáři podle hazardu
            if self.repo_material.add(name, price, hazard):
                messagebox.showinfo("Úspěch", f"Materiál '{name}' přidán (Kategorie přiřazena).")
                self.refresh_materials()
                self.entry_add_name.delete(0, 'end')
                self.entry_add_price.delete(0, 'end')
        except ValueError: messagebox.showerror("Chyba", "Cena musí být číslo!")

    def update_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            price = float(self.entry_edit_price.get())
            hazard = self.combo_edit_hazard.get()
            if self.repo_material.update_material(mat_id, price, hazard):
                messagebox.showinfo("Úspěch", "Aktualizováno.")
                self.refresh_materials()
        except ValueError: messagebox.showwarning("Chyba", "Vyber řádek a zadej cenu.")

    def delete_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            if self.repo_material.delete_material(mat_id):
                self.refresh_materials()
        except ValueError: pass

    def restore_material_action(self):
        try:
            mat_id = int(self.entry_edit_id.get())
            if self.repo_material.restore_material(mat_id):
                self.refresh_materials()
        except ValueError: pass

    # ==========================================
    # LOGIKA ZÁLOŽKY: KLIENTI
    # ==========================================
    def setup_clients_tab(self):
        # A: PŘIDÁNÍ
        frame_add = ttk.LabelFrame(self.tab_clients, text="➕ Přidat klienta")
        frame_add.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_add, text="Firma:").pack(side="left", padx=5)
        self.entry_c_name = ttk.Entry(frame_add, width=20)
        self.entry_c_name.pack(side="left", padx=5)

        ttk.Label(frame_add, text="Email:").pack(side="left", padx=5)
        self.entry_c_email = ttk.Entry(frame_add, width=20)
        self.entry_c_email.pack(side="left", padx=5)

        ttk.Label(frame_add, text="Kredit:").pack(side="left", padx=5)
        self.entry_c_credit = ttk.Entry(frame_add, width=10)
        self.entry_c_credit.pack(side="left", padx=5)

        ttk.Button(frame_add, text="Uložit", command=self.add_client_action).pack(side="left", padx=20)

        # B: TABULKA
        columns = ("id", "name", "email", "credit")
        self.tree_clients = ttk.Treeview(self.tab_clients, columns=columns, show="headings", height=10)
        self.tree_clients.heading("id", text="ID")
        self.tree_clients.heading("name", text="Firma")
        self.tree_clients.heading("email", text="Email")
        self.tree_clients.heading("credit", text="Kredit")
        
        self.tree_clients.column("id", width=50)
        self.tree_clients.pack(expand=True, fill="both", padx=10, pady=5)
        self.tree_clients.bind("<<TreeviewSelect>>", self.on_client_select)

        # C: ÚPRAVA
        frame_action = ttk.LabelFrame(self.tab_clients, text="✏️ Úprava klienta")
        frame_action.pack(fill="x", padx=10, pady=5)

        self.entry_c_edit_id = ttk.Entry(frame_action, width=5, state="readonly")
        self.entry_c_edit_id.pack(side="left", padx=5)

        self.entry_c_edit_name = ttk.Entry(frame_action, width=15)
        self.entry_c_edit_name.pack(side="left", padx=5)

        self.entry_c_edit_email = ttk.Entry(frame_action, width=15)
        self.entry_c_edit_email.pack(side="left", padx=5)

        self.entry_c_edit_credit = ttk.Entry(frame_action, width=10)
        self.entry_c_edit_credit.pack(side="left", padx=5)

        ttk.Button(frame_action, text="💾 Uložit", command=self.update_client_action).pack(side="left", padx=10)
        ttk.Button(frame_action, text="🗑️ Smazat", command=self.delete_client_action).pack(side="right", padx=10)
        ttk.Button(frame_action, text="🔄 Refresh", command=self.refresh_clients).pack(side="right", padx=10)

    def refresh_clients(self):
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        
        data = self.repo_client.get_all()
        for c in data:
            self.tree_clients.insert("", "end", values=(c.id, c.name, c.email, f"{c.credit:,.2f} Kč"))

    def on_client_select(self, event):
        selected = self.tree_clients.selection()
        if selected:
            values = self.tree_clients.item(selected)['values']
            self.entry_c_edit_id.config(state="normal")
            self.entry_c_edit_id.delete(0, 'end')
            self.entry_c_edit_id.insert(0, values[0])
            self.entry_c_edit_id.config(state="readonly")
            
            self.entry_c_edit_name.delete(0, 'end')
            self.entry_c_edit_name.insert(0, values[1])
            self.entry_c_edit_email.delete(0, 'end')
            self.entry_c_edit_email.insert(0, values[2])
            
            kredit_clean = str(values[3]).replace(" Kč", "").replace(",", "").replace("\xa0", "")
            self.entry_c_edit_credit.delete(0, 'end')
            self.entry_c_edit_credit.insert(0, kredit_clean)

    def add_client_action(self):
        try:
            name = self.entry_c_name.get()
            email = self.entry_c_email.get()
            credit = float(self.entry_c_credit.get())
            if self.repo_client.add(name, email, credit):
                messagebox.showinfo("Info", "Klient přidán.")
                self.refresh_clients()
        except ValueError: messagebox.showerror("Chyba", "Kredit musí být číslo.")

    def update_client_action(self):
        try:
            cid = int(self.entry_c_edit_id.get())
            name = self.entry_c_edit_name.get()
            email = self.entry_c_edit_email.get()
            credit = float(self.entry_c_edit_credit.get())
            if self.repo_client.update_client(cid, name, email, credit):
                messagebox.showinfo("Info", "Klient aktualizován.")
                self.refresh_clients()
        except ValueError: messagebox.showerror("Chyba", "Zkontroluj údaje.")

    def delete_client_action(self):
        try:
            cid = int(self.entry_c_edit_id.get())
            if messagebox.askyesno("Pozor", "Smazat klienta?"):
                success, msg = self.repo_client.delete_client(cid)
                if success:
                    self.refresh_clients()
                else:
                    messagebox.showerror("Chyba", msg)
        except ValueError: pass

    # ==========================================
    # LOGIKA ZÁLOŽKY: SEZNAM OBJEDNÁVEK (VIEW)
    # ==========================================
    def setup_orders_list_tab(self):
        frame_top = ttk.Frame(self.tab_orders_list)
        frame_top.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame_top, text="🔄 Aktualizovat", command=self.refresh_orders_list).pack(side="left")
        ttk.Button(frame_top, text="🗑️ Storno vybrané (Vrátit peníze)", command=self.delete_order_action).pack(side="right")

        columns = ("id", "client", "material", "qty", "price", "date")
        self.tree_orders = ttk.Treeview(self.tab_orders_list, columns=columns, show="headings", height=15)
        self.tree_orders.heading("id", text="ID")
        self.tree_orders.heading("client", text="Klient")
        self.tree_orders.heading("material", text="Materiál")
        self.tree_orders.heading("qty", text="Množství")
        self.tree_orders.heading("price", text="Cena celkem")
        self.tree_orders.heading("date", text="Datum")
        self.tree_orders.column("id", width=40)
        self.tree_orders.pack(expand=True, fill="both", padx=10, pady=5)

    def refresh_orders_list(self):
        for item in self.tree_orders.get_children():
            self.tree_orders.delete(item)
        data = self.repo_order.get_all_detailed()
        for o in data:
            cena = f"{o['total_price']:,.2f} Kč"
            self.tree_orders.insert("", "end", values=(o['id'], o['company_name'], o['material_name'], f"{o['quantity']} kg", cena, o['created_at']))

    def delete_order_action(self):
        selected = self.tree_orders.selection()
        if not selected: return
        oid = self.tree_orders.item(selected)['values'][0]
        if messagebox.askyesno("Storno", f"Stornovat objednávku č. {oid}?"):
            if self.repo_order.delete_order(oid):
                messagebox.showinfo("Hotovo", "Stornováno.")
                self.refresh_orders_list()
                self.refresh_report()

    # ==========================================
    # LOGIKA ZÁLOŽKY: NOVÁ OBJEDNÁVKA
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

        ttk.Button(frame, text="🚀 Odeslat Objednávku", command=self.create_order_action).grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")

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
                self.refresh_orders_list()
                self.entry_order_qty.delete(0, 'end')
            else:
                messagebox.showerror("Chyba", "Selhalo (zkontroluj kredit nebo ID).")
        except ValueError: messagebox.showerror("Chyba", "Zadej platná čísla.")

    # ==========================================
    # LOGIKA ZÁLOŽKY: REPORT
    # ==========================================
    def setup_report_tab(self):
        frame_buttons = ttk.Frame(self.tab_report)
        frame_buttons.pack(pady=5)
        ttk.Button(frame_buttons, text="🔄 Aktualizovat", command=self.refresh_report).pack(side="left", padx=5)
        ttk.Button(frame_buttons, text="📊 Manažerské Statistiky", command=self.show_detailed_report).pack(side="left", padx=5)

        columns = ("firma", "pocet", "celkem")
        self.tree_report = ttk.Treeview(self.tab_report, columns=columns, show="headings")
        self.tree_report.heading("firma", text="Firma")
        self.tree_report.heading("pocet", text="Počet Objednávek")
        self.tree_report.heading("celkem", text="Celková útrata")
        self.tree_report.pack(expand=True, fill="both", padx=10, pady=5)

    def refresh_report(self):
        for item in self.tree_report.get_children():
            self.tree_report.delete(item)
        try:
            data = self.repo_order.get_report()
            for row in data:
                self.tree_report.insert("", "end", values=(row[0], row[1], f"{row[2]:,.2f} Kč"))
        except: pass

    def show_detailed_report(self):
        import tkinter as tk
        report_window = tk.Toplevel(self)
        report_window.title("Manažerský Report")
        report_window.geometry("700x450")

        ttk.Label(report_window, text="📊 Souhrnný Report", font=("Arial", 16, "bold")).pack(pady=15)

        cols = ("Firma", "Počet Objednávek", "Celková Útrata", "Max Riziko")
        tree = ttk.Treeview(report_window, columns=cols, show="headings")
        tree.heading("Firma", text="Firma")
        tree.heading("Počet Objednávek", text="Počet Obj.")
        tree.heading("Celková Útrata", text="Celková Útrata")
        tree.heading("Max Riziko", text="Max Riziko")
        
        tree.column("Firma", width=150)
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        try:
            data = self.repo_order.get_summary_report()
            if not data: messagebox.showinfo("Info", "Zatím nejsou data.", parent=report_window)
            for row in data:
                tree.insert("", "end", values=(row[0], row[1], f"{row[2]:,.2f} Kč", row[3]))
        except Exception as e:
            messagebox.showerror("Chyba", f"{e}", parent=report_window)
        
        ttk.Button(report_window, text="Zavřít", command=report_window.destroy).pack(pady=15)

    # ==========================================
    # LOGIKA ZÁLOŽKY: ADMIN
    # ==========================================
    def setup_admin_tab(self):
        frame = ttk.Frame(self.tab_admin)
        frame.pack(padx=20, pady=20)
        ttk.Label(frame, text="Import dat ze souboru JSON", font=("Arial", 12)).pack(pady=10)
        ttk.Button(frame, text="📥 Spustit Import", command=self.run_import).pack(pady=10)

    def run_import(self):
        file_path = filedialog.askopenfilename(title="Vyberte JSON", filetypes=[("JSON", "*.json"), ("Vše", "*.*")])
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count_c, count_m = 0, 0
                for c in data.get('clients', []):
                    self.repo_client.add(c['name'], c['email'], c['credit'])
                    count_c += 1
                for m in data.get('materials', []):
                    # Zde jen předáváme data, is_active se nastaví na 1 defaultně v DB/Repo
                    self.repo_material.add(m['name'], m['price'], m['hazard'])
                    count_m += 1
                messagebox.showinfo("Import", f"Hotovo!\nKlientů: {count_c}\nMateriálů: {count_m}")
                self.refresh_materials()
                self.refresh_clients()
        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba při importu:\n{e}")

    def on_closing(self):
        if hasattr(self, 'connection') and self.connection:
            try: self.connection.close()
            except: pass
        self.destroy()