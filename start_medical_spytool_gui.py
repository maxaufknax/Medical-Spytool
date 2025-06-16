#!/usr/bin/env python3
"""
Starte die Medical Spytool GUI für den Benutzer.
"""

import sys
import os

# Add the source directory to Python path
source_dir = os.path.join(os.path.dirname(__file__), 'FINAL_DISTRIBUTION', 'Source')
sys.path.insert(0, source_dir)

def main():
    """Starte die Medical Spytool GUI."""
    try:
        print("🚀 Starte Medical Spytool v1.4-beta...")
        print("📊 Initialisierung der Komponenten...")
        
        import tkinter as tk
        from dnb_spytool.gui.main_window import DNBSpytoolGUI
        
        # Create root window
        root = tk.Tk()
        
        # Set window properties
        root.title("Medical Spytool v1.4-beta - Medizinische Publikationssuche")
        root.geometry("1200x800")
        root.minsize(800, 600)
        
        print("✅ GUI-Komponenten geladen")
        print("🔧 Initialisiere Datenbankverbindungen...")
        
        # Create GUI
        gui = DNBSpytoolGUI(root)
        
        print("✅ Medical Spytool erfolgreich gestartet!")
        print("\n" + "="*60)
        print("📖 WILLKOMMEN BEI MEDICAL SPYTOOL v1.4-beta")
        print("="*60)
        print("🔍 Durchsuchen Sie medizinische Publikationen aus:")
        print("   • Deutsche Nationalbibliothek (DNB)")
        print("   • PubMed (NCBI)")
        print("")
        print("✨ Neue Funktionen in v1.4:")
        print("   • Vollständige URL-Funktionalität")
        print("   • Erweiterte Analytics & Visualisierungen")
        print("   • Verbesserte Export-Optionen")
        print("   • Optimierte Benutzeroberfläche")
        print("")
        print("🎯 Erste Schritte:")
        print("   1. Gehen Sie zum 'Search' Tab")
        print("   2. Geben Sie einen Autorennamen ein")
        print("   3. Wählen Sie die Datenbank aus")
        print("   4. Klicken Sie auf 'Start Search'")
        print("="*60)
        print("")
        
        # Start main loop
        root.mainloop()
        
        print("👋 Medical Spytool wurde beendet. Auf Wiedersehen!")
        
    except Exception as e:
        print(f"❌ FEHLER beim Starten der Anwendung: {e}")
        import traceback
        traceback.print_exc()
        input("Drücken Sie Enter zum Beenden...")
        sys.exit(1)

if __name__ == "__main__":
    main()
