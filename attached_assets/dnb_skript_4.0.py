#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNB Publikations-Suchtool – Ultimate GUI
Erstellt von [Dein Name]

Dieses Skript bietet eine GUI-Anwendung zur Suche in der Deutschen Nationalbibliothek (DNB)
über die SRU-Schnittstelle. Es ruft seitenweise alle Treffer ab, parst die RDF/XML‑Antwort
und extrahiert ausgewählte Informationen, die anschließend in eine Excel‑Datei exportiert werden.
Zusätzlich lassen sich über den Personen‑Tab Suchanfragen (mit Namen, Suchbegriffen und
zusätzlichen Suchbegriffen) verwalten sowie gespeicherte Suchanfragen (Parameter) sichern und laden.
"""

##############################
# Imports und globale Einstellungen
##############################
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import json
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
import threading
import time
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

# Konfigurationsdatei
config_file = "dnb_config.json"

# Globale Variablen
persons = []                # Liste der Personen (jeder Eintrag ist ein Dictionary)
editing_person_index = None
search_results = []         # Gesammelte Suchergebnisse (Liste von Dictionaries)
settings = {}               # Einstellungen aus der Config-Datei
global_log = []             # Globaler Log (Liste von Logeinträgen)

# Datei für gespeicherte Suchanfragen
saved_queries_file = "saved_queries.json"

# Namespace-Dictionary für die DNB-Antwort
ns = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/'
}

##############################
# Einstellungen laden und speichern
##############################
def load_settings():
    global settings
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            log_message(None, "Einstellungen geladen.")
    except FileNotFoundError:
        settings = {
            "output_path": "./output",
            "unique_filenames": False,
            "output_columns": ["Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL"]
        }
        save_settings(settings["output_path"], settings["unique_filenames"], settings["output_columns"])
        log_message(None, "Standard-Einstellungen erstellt.")
    return settings.get("output_path", "./output")

def save_settings(output_path, unique_filenames, output_columns):
    settings["output_path"] = output_path
    settings["unique_filenames"] = unique_filenames
    settings["output_columns"] = output_columns
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    log_message(None, "Einstellungen gespeichert.")

##############################
# Funktionen für gespeicherte Suchanfragen
##############################
def load_saved_queries():
    try:
        with open(saved_queries_file, "r", encoding="utf-8") as f:
            queries = json.load(f)
        log_message(None, "Gespeicherte Suchanfragen geladen.")
        return queries
    except FileNotFoundError:
        log_message(None, "Keine gespeicherten Suchanfragen gefunden. Erstelle leere Liste.")
        return []
    except Exception as e:
        log_message(None, f"Fehler beim Laden der gespeicherten Suchanfragen: {e}")
        return []

def save_saved_queries(queries):
    try:
        with open(saved_queries_file, "w", encoding="utf-8") as f:
            json.dump(queries, f, indent=4)
        log_message(None, "Gespeicherte Suchanfragen gespeichert.")
    except Exception as e:
        log_message(None, f"Fehler beim Speichern der Suchanfragen: {e}")

##############################
# Logging-Funktionen (GUI und Konsole)
##############################
def log_message(log_widget, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    global_log.append(full_msg)
    if log_widget is not None:
        try:
            log_widget.config(state="normal")
            log_widget.insert(tk.END, full_msg)
            log_widget.see(tk.END)
            log_widget.config(state="disabled")
        except Exception as e:
            print("Logging-Fehler im GUI:", e)
    else:
        print(full_msg.strip())

def clear_log(log_widget):
    global global_log
    global_log = []
    log_widget.config(state="normal")
    log_widget.delete("1.0", tk.END)
    log_widget.config(state="disabled")

def export_log(log_widget):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text Dateien", "*.txt"), ("Alle Dateien", "*.*")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(global_log))
        messagebox.showinfo("Log exportiert", f"Log wurde in {file_path} gespeichert.")

##############################
# Hilfsfunktion: Query transformieren (CQL-Format für DNB)
##############################
def transform_query(search_term):
    if not search_term.lower().startswith("dc.any"):
        parts = search_term.split()
        if len(parts) == 2:
            return f'dc.any all ("{search_term}" or "{parts[1]}, {parts[0]}")'
        else:
            return f'dc.any all "{search_term}"'
    return search_term

##############################
# DNB Suchfunktionen inkl. Paging und erweitertem Logging
##############################
def search_dnb_page(query, start_record, page_size=1000):
    base_url = "https://services.dnb.de/sru/dnb"
    params = {
        "version": "1.1",
        "operation": "searchRetrieve",
        "query": query,
        "recordSchema": "RDFxml",
        "maximumRecords": str(page_size),
        "startRecord": str(start_record)
    }
    log_message(None, f"Sende DNB-Anfrage: startRecord={start_record}, page_size={page_size}, query={query}")
    response = requests.get(base_url, params=params)
    log_message(None, f"Antwortstatus: {response.status_code}")
    response.raise_for_status()
    return response.text

def get_all_dnb_results(query, page_size=1000):
    all_results = []
    start_record = 1
    total_records = None
    log_message(None, f"Starte Abruf aller Treffer für Query: {query}")
    while True:
        try:
            xml_text = search_dnb_page(query, start_record, page_size)
        except Exception as e:
            log_message(None, f"Fehler beim Abruf ab Datensatz {start_record}: {e}")
            break

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            log_message(None, f"XML Parsing Fehler ab Datensatz {start_record}: {e}")
            break

        num_elem = root.find('.//srw:numberOfRecords', ns)
        if num_elem is not None and num_elem.text:
            total_records = int(num_elem.text)
            log_message(None, f"Gesamtanzahl der Treffer laut DNB: {total_records}")
        else:
            total_records = 0
            log_message(None, "Gesamtanzahl der Treffer konnte nicht ermittelt werden.")

        page_results = parse_dnb_response(xml_text)
        all_results.extend(page_results)
        log_message(None, f"Abfrage ab Datensatz {start_record}: {len(page_results)} Treffer gefunden.")
        if total_records is not None and start_record + page_size > total_records:
            break
        start_record += page_size
        time.sleep(1)  # kurze Pause zwischen Requests
    log_message(None, f"Gesamtabfrage abgeschlossen: {len(all_results)} Treffer insgesamt.")
    return all_results

def parse_dnb_response(xml_text):
    """
    Parst die RDF/XML-Antwort der DNB und extrahiert folgende Felder:
      - Titel (dc:title)
      - Creator (erst dc:creator, dann dcterms:creator, dann rdau:P60327)
      - Erscheinungsjahr (dcterms:issued)
      - Identifier (erstes dc:identifier)
      - URL (foaf:isPrimaryTopicOf)
    Liefert eine Liste von Dictionaries.
    """
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        log_message(None, f"XML Parsing Fehler in parse_dnb_response: {e}")
        return results

    records = root.findall('.//srw:record', ns)
    if not records:
        log_message(None, "Keine <record>-Elemente gefunden in der Antwort.")
        return results

    for record in records:
        record_data = record.find('srw:recordData', ns)
        if record_data is None:
            continue
        rdf_elem = record_data.find('rdf:RDF', ns)
        if rdf_elem is None:
            continue
        # Suche nach dem ersten rdf:Description mit einem dc:title
        desc = None
        for d in rdf_elem.findall('rdf:Description', ns):
            if d.find('dc:title', ns) is not None:
                desc = d
                break
        if desc is None:
            continue

        title_elem = desc.find('dc:title', ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Kein Titel"

        # Creator: Versuche dc:creator, dann dcterms:creator, dann rdau:P60327
        creator = ""
        creator_elem = desc.find('dc:creator', ns)
        if creator_elem is not None and creator_elem.text:
            creator = creator_elem.text.strip()
        else:
            creator_elem = desc.find('dcterms:creator', ns)
            if creator_elem is not None and creator_elem.text:
                creator = creator_elem.text.strip()
            else:
                creator_elem = desc.find('rdau:P60327', ns)
                if creator_elem is not None and creator_elem.text:
                    creator = creator_elem.text.strip()
                else:
                    creator = "Kein Creator"

        issued_elem = desc.find('dcterms:issued', ns)
        issued = issued_elem.text.strip() if issued_elem is not None and issued_elem.text else ""

        id_elem = desc.find('dc:identifier', ns)
        identifier = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

        url_elem = desc.find('foaf:isPrimaryTopicOf', ns)
        url = url_elem.text.strip() if url_elem is not None and url_elem.text else ""

        results.append({
            "Titel": title,
            "Creator": creator,
            "Erscheinungsjahr": issued,
            "Identifier": identifier,
            "URL": url
        })
    log_message(None, f"parse_dnb_response: {len(results)} Datensätze erfolgreich geparst.")
    return results

##############################
# GUI-Klasse für DNB-Suche
##############################
class DNB_GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("DNB Publikations-Suchtool - Ultimate GUI")
        self.master.geometry("1200x800")
        self.search_results = []
        self.output_path = load_settings()
        self.pause_flag = False
        self.stop_flag = False
        self.create_widgets()

    def create_widgets(self):
        # Notebook mit Tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab: Personen & Suche
        self.tab_person = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_person, text="Personen & Suche")
        self.create_person_tab()

        # Tab: DNB Suche (Einzelsuche)
        self.tab_search = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_search, text="DNB Suche (Einzelsuche)")
        self.create_search_tab()

        # Tab: Erweiterte Optionen
        self.tab_options = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_options, text="Erweiterte Optionen")
        self.create_options_tab()

        # Tab: Ausgabe
        self.tab_output = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_output, text="Ausgabe")
        self.create_output_tab()

        # Tab: Suchergebnisse
        self.tab_results = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_results, text="Suchergebnisse")
        self.create_results_tab()

        # Tab: Gespeicherte Suchen
        self.tab_saved = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_saved, text="Gespeicherte Suchen")
        self.create_saved_queries_tab()

        # Tab: Log
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text="Log")
        self.create_log_tab()

        # Tab: Einstellungen
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="Einstellungen")
        self.create_settings_tab()

        # Tab: Analyse
        self.tab_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analysis, text="Analyse")
        self.create_analysis_tab()

        # Menüleiste
        self.create_menu_bar()

        # Steuerungsbereich unten
        self.control_frame = ttk.Frame(self.master)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.create_control_buttons()

    ##############################
    # Tab "Personen & Suche" – Personenverwaltung
    ##############################
    def create_person_tab(self):
        frame_input = ttk.LabelFrame(self.tab_person, text="Person hinzufügen/bearbeiten", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame_input, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_name = ttk.Entry(frame_input, width=40)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_input, text="Suchbegriff:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_person_query = ttk.Entry(frame_input, width=40)
        self.entry_person_query.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_input, text="Weitere Suchbegriffe:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_person_additional = ttk.Entry(frame_input, width=40)
        self.entry_person_additional.grid(row=2, column=1, padx=5, pady=5)

        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=3, column=0, columnspan=2, pady=5)
        self.btn_add = ttk.Button(frame_buttons, text="Hinzufügen", command=self.add_person)
        self.btn_add.pack(side=tk.LEFT, padx=5)
        self.btn_edit = ttk.Button(frame_buttons, text="Bearbeiten", command=self.edit_person)
        self.btn_edit.pack(side=tk.LEFT, padx=5)
        self.btn_delete = ttk.Button(frame_buttons, text="Löschen", command=self.delete_person)
        self.btn_delete.pack(side=tk.LEFT, padx=5)
        self.btn_save = ttk.Button(frame_buttons, text="Änderungen speichern", command=self.save_person_changes)
        self.btn_save.pack(side=tk.LEFT, padx=5)
        self.btn_save.config(state="disabled")

        frame_tree = ttk.LabelFrame(self.tab_person, text="Personenliste", padding=10)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("Name", "Suchbegriff", "Weitere Suchbegriffe")
        self.tree_persons = ttk.Treeview(frame_tree, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree_persons.heading(col, text=col)
            if col == "Name":
                self.tree_persons.column(col, width=200)
            elif col == "Suchbegriff":
                self.tree_persons.column(col, width=300)
            else:
                self.tree_persons.column(col, width=200)
        self.tree_persons.pack(fill=tk.BOTH, expand=True)

        frame_imp_exp = ttk.Frame(self.tab_person)
        frame_imp_exp.pack(fill=tk.X, padx=10, pady=5)
        self.btn_import = ttk.Button(frame_imp_exp, text="Importieren", command=self.import_persons)
        self.btn_import.pack(side=tk.LEFT, padx=5)
        self.btn_export = ttk.Button(frame_imp_exp, text="Exportieren", command=self.export_persons)
        self.btn_export.pack(side=tk.LEFT, padx=5)

    def add_person(self):
        name = self.entry_name.get().strip()
        query = self.entry_person_query.get().strip()
        additional = self.entry_person_additional.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        person = {"name": name, "search_term": query, "additional_search": additional}
        persons.append(person)
        self.update_person_tree()
        self.clear_person_inputs()
        log_message(self.text_log, f"Person '{name}' hinzugefügt.")

    def edit_person(self):
        selected = self.tree_persons.selection()
        if not selected:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine Person aus.")
            return
        idx = int(selected[0])
        person = persons[idx]
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, person["name"])
        self.entry_person_query.delete(0, tk.END)
        self.entry_person_query.insert(0, person["search_term"])
        self.entry_person_additional.delete(0, tk.END)
        self.entry_person_additional.insert(0, person.get("additional_search", ""))
        global editing_person_index
        editing_person_index = idx
        self.btn_add.config(state="disabled")
        self.btn_save.config(state="normal")
        log_message(self.text_log, f"Person '{person['name']}' zum Bearbeiten geladen.")

    def save_person_changes(self):
        global editing_person_index
        if editing_person_index is None:
            messagebox.showwarning("Keine Auswahl", "Keine Person ausgewählt.")
            return
        name = self.entry_name.get().strip()
        query = self.entry_person_query.get().strip()
        additional = self.entry_person_additional.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        persons[editing_person_index] = {"name": name, "search_term": query, "additional_search": additional}
        self.update_person_tree()
        self.clear_person_inputs()
        editing_person_index = None
        self.btn_add.config(state="normal")
        self.btn_save.config(state="disabled")
        log_message(self.text_log, f"Änderungen für '{name}' gespeichert.")

    def delete_person(self):
        selected = self.tree_persons.selection()
        if not selected:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine Person aus.")
            return
        idx = int(selected[0])
        del persons[idx]
        self.update_person_tree()
        self.clear_person_inputs()
        log_message(self.text_log, "Person gelöscht.")

    def update_person_tree(self):
        for item in self.tree_persons.get_children():
            self.tree_persons.delete(item)
        for i, p in enumerate(persons):
            self.tree_persons.insert("", tk.END, iid=str(i), values=(p["name"], p["search_term"], p.get("additional_search", "")))

    def clear_person_inputs(self):
        self.entry_name.delete(0, tk.END)
        self.entry_person_query.delete(0, tk.END)
        self.entry_person_additional.delete(0, tk.END)

    def import_persons(self):
        file_path = filedialog.askopenfilename(defaultextension=".json",
                                               filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                global persons
                persons = imported
                self.update_person_tree()
                messagebox.showinfo("Import erfolgreich", f"Personenliste aus {file_path} geladen.")
                log_message(self.text_log, "Personenliste importiert.")
            except Exception as e:
                messagebox.showerror("Import Fehler", f"Fehler beim Importieren: {e}")

    def export_persons(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(persons, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Export erfolgreich", f"Personenliste nach {file_path} exportiert.")
                log_message(self.text_log, "Personenliste exportiert.")
            except Exception as e:
                messagebox.showerror("Export Fehler", f"Fehler beim Exportieren: {e}")

    ##############################
    # Tab "DNB Suche (Einzelsuche)"
    ##############################
    def create_search_tab(self):
        frame_input = ttk.LabelFrame(self.tab_search, text="DNB Suchparameter (Einzelsuche)", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_input, text="Suchbegriff:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_query = ttk.Entry(frame_input, width=40)
        self.entry_query.grid(row=0, column=1, padx=5, pady=5)
        self.entry_query.insert(0, "Anette Melk")  # Standardwert

    ##############################
    # Tab "Erweiterte Optionen"
    ##############################
    def create_options_tab(self):
        frame_opts = ttk.LabelFrame(self.tab_options, text="Suchparameter", padding=10)
        frame_opts.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_opts, text="Startdatum:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_start_date = DateEntry(frame_opts, width=12, date_pattern='yyyy-mm-dd')
        self.entry_start_date.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_opts, text="Enddatum:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_end_date = DateEntry(frame_opts, width=12, date_pattern='yyyy-mm-dd')
        self.entry_end_date.grid(row=0, column=3, padx=5, pady=5)
        # Kontrollkästchen zum Ein-/Ausschalten des Datumsfilters
        self.var_date_filter = tk.BooleanVar(value=True)
        chk_date = ttk.Checkbutton(frame_opts, text="Datumfilter aktivieren", variable=self.var_date_filter)
        chk_date.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(frame_opts, text="Ausgabeformat:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.combo_format = ttk.Combobox(frame_opts, values=["Excel (.xlsx)", "CSV (.csv)"], state="readonly", width=15)
        self.combo_format.current(0)
        self.combo_format.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(frame_opts, text="Ausgabepfad:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_output_path = ttk.Entry(frame_opts, width=40)
        self.entry_output_path.grid(row=3, column=1, padx=5, pady=5, columnspan=2)
        self.btn_browse = ttk.Button(frame_opts, text="Durchsuchen", command=self.select_output_path)
        self.btn_browse.grid(row=3, column=3, padx=5, pady=5)
        ttk.Label(frame_opts, text="Sprache (optional):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.entry_language = ttk.Entry(frame_opts, width=10)
        self.entry_language.grid(row=4, column=1, padx=5, pady=5)

    ##############################
    # Tab "Ausgabe" – Spaltenauswahl
    ##############################
    def create_output_tab(self):
        frame_output = ttk.LabelFrame(self.tab_output, text="Ausgabe-Einstellungen", padding=10)
        frame_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        ttk.Label(frame_output, text="Wählen Sie die Ausgabespalten:").pack(anchor="w", pady=(0,5))
        frame_checkbuttons = ttk.Frame(frame_output)
        frame_checkbuttons.pack(fill=tk.BOTH, expand=True)
        self.available_columns = ["Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL"]
        self.output_vars = {}
        columns_per_row = 2
        for idx, col in enumerate(self.available_columns):
            var = tk.BooleanVar(value=True)
            self.output_vars[col] = var
            chk = ttk.Checkbutton(frame_checkbuttons, text=col, variable=var)
            chk.grid(row=idx // columns_per_row, column=idx % columns_per_row, sticky="w", padx=5, pady=2)

    ##############################
    # Tab "Suchergebnisse"
    ##############################
    def create_results_tab(self):
        frame_results = ttk.LabelFrame(self.tab_results, text="Suchergebnisse", padding=10)
        frame_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = ["Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL"]
        self.tree_results = ttk.Treeview(frame_results, columns=cols, show="headings")
        for col in cols:
            self.tree_results.heading(col, text=col)
            self.tree_results.column(col, width=200, anchor="w")
        # Vertikaler Scrollbalken
        vsb = ttk.Scrollbar(frame_results, orient="vertical", command=self.tree_results.yview)
        self.tree_results.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Horizontaler Scrollbalken
        hsb = ttk.Scrollbar(frame_results, orient="horizontal", command=self.tree_results.xview)
        self.tree_results.configure(xscrollcommand=hsb.set)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.btn_export_results = ttk.Button(self.tab_results, text="Ergebnisse exportieren", command=self.export_results)
        self.btn_export_results.pack(pady=5)

    ##############################
    # Tab "Gespeicherte Suchen"
    ##############################
    def create_saved_queries_tab(self):
        frame_saved = ttk.LabelFrame(self.tab_saved, text="Gespeicherte Suchanfragen", padding=10)
        frame_saved.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # Listbox mit Scrollbalken
        self.listbox_saved = tk.Listbox(frame_saved, height=10)
        vsb_saved = ttk.Scrollbar(frame_saved, orient="vertical", command=self.listbox_saved.yview)
        self.listbox_saved.configure(yscrollcommand=vsb_saved.set)
        self.listbox_saved.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        vsb_saved.pack(side=tk.LEFT, fill=tk.Y)
        # Buttons für Speichern, Laden und Löschen
        frame_saved_buttons = ttk.Frame(self.tab_saved)
        frame_saved_buttons.pack(fill=tk.X, padx=10, pady=5)
        self.btn_save_query = ttk.Button(frame_saved_buttons, text="Aktuelle Suche speichern", command=self.save_current_query)
        self.btn_save_query.pack(side=tk.LEFT, padx=5)
        self.btn_load_query = ttk.Button(frame_saved_buttons, text="Ausgewählte laden", command=self.load_selected_query)
        self.btn_load_query.pack(side=tk.LEFT, padx=5)
        self.btn_delete_query = ttk.Button(frame_saved_buttons, text="Ausgewählte löschen", command=self.delete_selected_query)
        self.btn_delete_query.pack(side=tk.LEFT, padx=5)
        self.refresh_saved_queries_listbox()

    def save_current_query(self):
        # Hole die aktuellen Suchparameter aus den Tabs "DNB Suche (Einzelsuche)" und "Erweiterte Optionen"
        query = self.entry_query.get().strip()
        start_date = self.entry_start_date.get().strip()
        end_date = self.entry_end_date.get().strip()
        date_filter = self.var_date_filter.get()
        language = self.entry_language.get().strip()
        # Als Display-Name verwenden wir den Suchbegriff
        display_name = query if query else "Ohne Suchbegriff"
        saved_query = {
            "display_name": display_name,
            "search_term": query,
            "start_date": start_date,
            "end_date": end_date,
            "date_filter": date_filter,
            "language": language
        }
        current_queries = load_saved_queries()
        current_queries.append(saved_query)
        save_saved_queries(current_queries)
        self.refresh_saved_queries_listbox()
        log_message(self.text_log, f"Gespeicherte Suchanfrage '{display_name}' hinzugefügt.")

    def refresh_saved_queries_listbox(self):
        self.listbox_saved.delete(0, tk.END)
        queries = load_saved_queries()
        for q in queries:
            display = f"{q.get('display_name', '')} - {q.get('search_term', '')}"
            self.listbox_saved.insert(tk.END, display)

    def load_selected_query(self):
        selection = self.listbox_saved.curselection()
        if not selection:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine gespeicherte Suchanfrage aus.")
            return
        index = selection[0]
        queries = load_saved_queries()
        if index < len(queries):
            q = queries[index]
            self.entry_query.delete(0, tk.END)
            self.entry_query.insert(0, q.get("search_term", ""))
            self.entry_start_date.set_date(q.get("start_date", datetime.now()))
            self.entry_end_date.set_date(q.get("end_date", datetime.now()))
            self.var_date_filter.set(q.get("date_filter", True))
            self.entry_language.delete(0, tk.END)
            self.entry_language.insert(0, q.get("language", ""))
            log_message(self.text_log, f"Gespeicherte Suchanfrage '{q.get('display_name', '')}' geladen.")

    def delete_selected_query(self):
        selection = self.listbox_saved.curselection()
        if not selection:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine gespeicherte Suchanfrage aus.")
            return
        index = selection[0]
        queries = load_saved_queries()
        if index < len(queries):
            q = queries.pop(index)
            save_saved_queries(queries)
            self.refresh_saved_queries_listbox()
            log_message(self.text_log, f"Gespeicherte Suchanfrage '{q.get('display_name', '')}' gelöscht.")

    ##############################
    # Tab "Log"
    ##############################
    def create_log_tab(self):
        frame_log = ttk.Frame(self.tab_log)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_log = tk.Text(frame_log, wrap="none", state="disabled", height=15)
        vsb_log = ttk.Scrollbar(frame_log, orient="vertical", command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=vsb_log.set)
        self.text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb_log.pack(side=tk.RIGHT, fill=tk.Y)
        frame_log_buttons = ttk.Frame(self.tab_log)
        frame_log_buttons.pack(fill=tk.X, padx=10, pady=5)
        self.btn_clear_log = ttk.Button(frame_log_buttons, text="Log leeren", command=lambda: clear_log(self.text_log))
        self.btn_clear_log.pack(side=tk.LEFT, padx=5)
        self.btn_export_log = ttk.Button(frame_log_buttons, text="Log exportieren", command=lambda: export_log(self.text_log))
        self.btn_export_log.pack(side=tk.LEFT, padx=5)

    ##############################
    # Tab "Einstellungen"
    ##############################
    def create_settings_tab(self):
        frame_settings = ttk.LabelFrame(self.tab_settings, text="Einstellungen", padding=10)
        frame_settings.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_settings, text="API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_api_key = ttk.Entry(frame_settings, width=40)
        self.entry_api_key.grid(row=0, column=1, padx=5, pady=5)
        # Für DNB wird in der Regel kein API-Key benötigt
        self.entry_api_key.insert(0, "")
        ttk.Label(frame_settings, text="Ausgabespalten (Komma-getrennt):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_output_columns = ttk.Entry(frame_settings, width=60)
        self.entry_output_columns.grid(row=1, column=1, padx=5, pady=5)
        current_columns = settings.get("output_columns", [])
        self.entry_output_columns.insert(0, ", ".join(current_columns))
        self.btn_save_settings = ttk.Button(frame_settings, text="Einstellungen speichern", command=self.save_gui_settings)
        self.btn_save_settings.grid(row=2, column=0, columnspan=2, pady=10)

    def save_gui_settings(self):
        new_api_key = self.entry_api_key.get().strip()
        new_output_columns = [col.strip() for col in self.entry_output_columns.get().split(",") if col.strip()]
        global API_KEY
        API_KEY = new_api_key
        current_output = load_settings()
        save_settings(current_output, settings.get("unique_filenames", False), new_output_columns)
        messagebox.showinfo("Einstellungen", "Die Einstellungen wurden erfolgreich gespeichert.")
        log_message(self.text_log, "Einstellungen aktualisiert.")

    ##############################
    # Tab "Analyse"
    ##############################
    def create_analysis_tab(self):
        frame_analysis = ttk.LabelFrame(self.tab_analysis, text="Analyse der Suchergebnisse", padding=10)
        frame_analysis.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.analysis_text = tk.Text(frame_analysis, wrap="word", state="disabled", height=10)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        frame_analysis_buttons = ttk.Frame(self.tab_analysis)
        frame_analysis_buttons.pack(fill=tk.X, padx=10, pady=5)
        self.btn_run_analysis = ttk.Button(frame_analysis_buttons, text="Analyse aktualisieren", command=self.run_analysis)
        self.btn_run_analysis.pack(side=tk.LEFT, padx=5)
        self.btn_show_chart = ttk.Button(frame_analysis_buttons, text="Diagramm anzeigen", command=self.display_chart)
        self.btn_show_chart.pack(side=tk.LEFT, padx=5)

    def run_analysis(self):
        total = len(self.search_results)
        results_per_person = {}
        for result in self.search_results:
            person = result.get("Name", "Unbekannt")
            results_per_person[person] = results_per_person.get(person, 0) + 1
        report = f"Gesamtanzahl der Ergebnisse: {total}\n\nErgebnisse pro Person:\n"
        for person, count in results_per_person.items():
            report += f"  - {person}: {count}\n"
        self.analysis_text.config(state="normal")
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, report)
        self.analysis_text.config(state="disabled")
        log_message(self.text_log, "Analyse der Suchergebnisse aktualisiert.")

    def display_chart(self):
        if not self.search_results:
            messagebox.showinfo("Analyse", "Keine Daten für das Diagramm vorhanden.")
            return
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(["Ergebnisse"], [len(self.search_results)], color="skyblue")
        ax.set_title("Anzahl der Ergebnisse")
        plt.tight_layout()
        if hasattr(self, "chart_canvas"):
            self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.tab_analysis)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        log_message(self.text_log, "Diagramm aktualisiert.")

    ##############################
    # Steuerungsbuttons + Statusleiste
    ##############################
    def create_control_buttons(self):
        self.btn_start = ttk.Button(self.control_frame, text="Suche starten", command=self.start_search)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_pause = ttk.Button(self.control_frame, text="Pause", command=self.pause_search, state="disabled")
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_stop = ttk.Button(self.control_frame, text="Stop", command=self.stop_search, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.control_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.status_label = ttk.Label(self.control_frame, text="Status: Idle")
        self.status_label.pack(fill=tk.X, padx=5, pady=(5,0))

    ##############################
    # Suchvorgang starten (Threading)
    ##############################
    def start_search(self):
        # Verwende, falls vorhanden, die Personenliste; ansonsten Einzel-Suche
        if persons:
            search_list = persons
        else:
            display_name = self.entry_query.get().strip()
            person = {
                "name": display_name,
                "search_term": self.entry_query.get().strip(),
                "additional_search": ""
            }
            search_list = [person]
        if not search_list:
            messagebox.showwarning("Keine Personen", "Bitte fügen Sie mindestens eine Person hinzu oder geben Sie einen Suchbegriff ein.")
            return
        if not self.entry_output_path.get().strip():
            messagebox.showwarning("Ausgabepfad", "Bitte wählen Sie einen Ausgabepfad in den erweiterten Optionen.")
            return

        self.search_results = []
        self.update_results_tree()
        self.progress_var.set(0)
        self.pause_flag = False
        self.stop_flag = False
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")
        self.search_start_time = time.time()

        total = len(search_list)
        for idx, person in enumerate(search_list):
            if self.stop_flag:
                log_message(self.text_log, "Suche abgebrochen.")
                break
            while self.pause_flag:
                time.sleep(0.5)
            # Transformiere den Suchbegriff in CQL-Format
            base_query = transform_query(person["search_term"])
            additional = person.get("additional_search", "")
            if additional:
                final_query = f"({base_query}) AND ({additional})"
            else:
                final_query = base_query

            # Falls der Datumfilter aktiviert ist, füge diesen hinzu
            if self.var_date_filter.get():
                start_date = self.entry_start_date.get().strip() or None
                end_date = self.entry_end_date.get().strip() or None
                if start_date and end_date:
                    start_date_fmt = start_date.replace("-", "/")
                    end_date_fmt = end_date.replace("-", "/")
                    final_query += f" AND (\"{start_date_fmt}\"[Date - Publication] : \"{end_date_fmt}\"[Date - Publication])"
            # Optionale Sprache hinzufügen
            lang = self.entry_language.get().strip()
            if lang:
                final_query += f" AND language={lang}"

            log_message(self.text_log, f"Suche für {person['name']} mit Query: {final_query}")
            try:
                results = get_all_dnb_results(final_query, page_size=1000)
            except Exception as e:
                log_message(self.text_log, f"Fehler bei der Suche für {person['name']}: {e}")
                continue
            # Füge den Anzeige-Namen zu jedem Ergebnis hinzu
            for res in results:
                res["Name"] = person["name"]
            self.search_results.extend(results)
            progress = ((idx + 1) / total) * 100
            self.master.after(0, self.progress_var.set, progress)
            self.master.after(0, self.update_results_tree)
            elapsed = time.time() - self.search_start_time
            completed = idx + 1
            estimated_total = elapsed / completed * total if completed > 0 else 0
            remaining = estimated_total - elapsed
            results_count = len(self.search_results)
            current_person = person["name"]
            self.master.after(0, self.update_status, current_person, progress, results_count, remaining)
            log_message(self.text_log, f"Suche für {person['name']} abgeschlossen ({len(results)} Ergebnisse).")
            time.sleep(0.2)
        self.master.after(0, self.search_finished)

    def pause_search(self):
        self.pause_flag = not self.pause_flag
        if self.pause_flag:
            self.btn_pause.config(text="Weiter")
            log_message(self.text_log, "Suche pausiert.")
        else:
            self.btn_pause.config(text="Pause")
            log_message(self.text_log, "Suche fortgesetzt.")

    def stop_search(self):
        self.stop_flag = True
        self.btn_stop.config(state="disabled")
        log_message(self.text_log, "Stop-Befehl empfangen. Suche wird abgebrochen.")

    def search_finished(self):
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="Pause")
        self.btn_stop.config(state="disabled")
        self.progress_var.set(100)
        self.update_status("Fertig", 100, len(self.search_results), 0)
        log_message(self.text_log, "Alle Suchvorgänge abgeschlossen.")

    def update_status(self, current, progress, count, remaining):
        status_text = f"Verarbeite: {current} | Fortschritt: {progress:.1f}% | Ergebnisse: {count} | Verbleibende Zeit: {remaining:.0f} s"
        self.status_label.config(text=status_text)

    def update_results_tree(self):
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
        for i, result in enumerate(self.search_results):
            values = (
                result.get("Name", ""),
                result.get("Titel", ""),
                result.get("Creator", ""),
                result.get("Erscheinungsjahr", ""),
                result.get("Identifier", ""),
                result.get("URL", "")
            )
            self.tree_results.insert("", tk.END, iid=str(i), values=values)

    def export_results(self):
        out_path = self.entry_output_path.get().strip()
        if not out_path:
            messagebox.showwarning("Ausgabepfad", "Bitte wählen Sie einen Ausgabepfad in den erweiterten Optionen.")
            return
        df = pd.DataFrame(self.search_results)
        selected_columns = [col for col, var in self.output_vars.items() if var.get()]
        for col in selected_columns:
            if col not in df.columns:
                df[col] = ""
        df = df[selected_columns]
        try:
            if self.combo_format.get() == "Excel (.xlsx)":
                df.to_excel(out_path, index=False)
            else:
                df.to_csv(out_path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("Export erfolgreich", f"Ergebnisse wurden exportiert nach {out_path}")
            log_message(self.text_log, f"Ergebnisse exportiert nach {out_path}")
        except Exception as e:
            messagebox.showerror("Export Fehler", f"Fehler beim Export: {e}")
            log_message(self.text_log, f"Export Fehler: {e}")

    def select_output_path(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel Dateien", "*.xlsx"), ("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")])
        if file_path:
            self.entry_output_path.delete(0, tk.END)
            self.entry_output_path.insert(0, file_path)
            current_output = load_settings()
            save_settings(os.path.dirname(file_path), settings.get("unique_filenames", False), settings.get("output_columns", []))
            self.output_path = os.path.dirname(file_path)
            log_message(self.text_log, f"Ausgabepfad gesetzt auf: {file_path}")

    def create_menu_bar(self):
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Beenden", command=self.master.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Über", command=self.show_about)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        self.master.config(menu=menubar)

    def show_about(self):
        messagebox.showinfo("Über", "DNB Publikations-Suchtool\nVersion 1.1\nErstellt von [Dein Name]")

##############################
# Ende der Klasse DNB_GUI
##############################

def main():
    root = tk.Tk()
    app = DNB_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
