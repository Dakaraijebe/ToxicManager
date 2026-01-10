import sys
import os

# 1. Nastavíme cestu, aby Python viděl složku 'src'
sys.path.append(os.getcwd())

# 2. Importujeme naši novou třídu okna
try:
    from src.GUI.AppWindow import ToxicManagerGUI
except ImportError as e:
    print(f"KRITICKÁ CHYBA: {e}")
    print("Ujisti se, že máš složku src/GUI a v ní AppWindow.py")
    sys.exit(1)

# 3. Spustíme aplikaci
if __name__ == "__main__":
    app = ToxicManagerGUI()
    
    # Nastavíme, co se stane při křížku (aby se odpojila DB)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Nekonečná smyčka okna
    app.mainloop()