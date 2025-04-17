#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" DFG GEPRIS Publikations-Suchtool – Ultimate GUI Erstellt von [Ihr Name]

Dieses Skript bietet eine GUI-Anwendung zur Suche in der DFG GEPRIS-Datenbank. Das Design (Tabs, Einstellungen, Log, Analyse) orientiert sich an den bisherigen Skripten. Die Suchfunktion baut eine Anfrage an den angenommenen GEPRIS-Endpunkt (https://gepris.dfg.de/gepris/OCTOPUS) und parst die XML-Antwort, um alle verfügbaren Informationen zu extrahieren. """

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import json
import threading
import time
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Globale Einstellungen
CONFIG_FILE = "gepris_config.json"
global_log = []  # Globaler Log
settings = {}  # Globale Settings-Variable
editing_person_index = None  # Global für die Personenbearbeitung

# Einstellungen laden und speichern
def load_settings():
    global settings
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            "output_path": "./output",
            "unique_filenames": False,
            "output_columns": ["Name", "Projekt Titel", "Projekt ID", "Förderjahr", "Projektleiter", "Institution", "Beschreibung", "GEPRIS URL"]
        }
        save_settings(settings["output_path"], settings["unique_filenames"], settings["output_columns"])
    return settings.get("output_path", "./output")

def save_settings(output_path, unique_filenames, output_columns):
    global settings
    settings["output_path"] = output_path
    settings["unique_filenames"] = unique_filenames
    settings["output_columns"] = output_columns
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

# Logging-Funktionen
def log_message(log_widget, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    global_log.append(full_msg)
    if log_widget:
        log_widget.config(state="normal")
        log_widget.insert(tk.END, full_msg)
        log_widget.see(tk.END)
        log_widget.config(state="disabled")
    else:
        print(full_msg.strip())

def clear_log(log_widget):
    global global_log
    global_log = []
    log_widget.config(state="normal")
    log_widget.delete("1.0", tk.END)
    log_widget.config(state="disabled")

def export_log(log_widget):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Dateien", ".txt"), ("Alle Dateien", ".*")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(global_log))
        messagebox.showinfo("Log exportiert", f"Log wurde in {file_path} gespeichert.")

# GEPRIS Suchfunktion
def search_gepris(query, name, max_results=100):
    """ Führt eine Suche in der DFG GEPRIS-Datenbank durch.
    Angenommene URL: https://gepris.dfg.de/gepris/OCTOPUS
    Erwartet eine XML-Antwort, die folgende Felder enthalten kann:
    - Projekt Titel
    - Projekt ID
    - Förderjahr
    - Projektleiter
    - Institution
    - Beschreibung
    - GEPRIS URL """
    base_url = "https://gepris.dfg.de/gepris/OCTOPUS"
    params = {
        "query": query,
        "max": max_results,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        xml_text = response.text
    except Exception as e:
        log_message(None, f"Fehler bei GEPRIS-Suche für Query '{query}': {e}")
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        log_message(None, f"XML Parsing Fehler: {e}")
        return []

    publications = []
    # Annahme: Jedes Projekt ist in einem <project>-Element enthalten.
    for proj in root.findall(".//project"):
        try:
            title = proj.findtext("title", default="Kein Titel")
            proj_id = proj.findtext("id", default="Keine ID")
            funding_year = proj.findtext("fundingYear", default="Kein Jahr")
            leader = proj.findtext("projectLeader", default="Kein Projektleiter")
            institution = proj.findtext("institution", default="Keine Institution")
            description = proj.findtext("description", default="Keine Beschreibung")
            gepris_url = proj.findtext("url", default="Keine GEPRIS URL")
            publications.append({
                "Name": name,
                "Projekt Titel": title,
                "Projekt ID": proj_id,
                "Förderjahr": funding_year,
                "Projektleiter": leader,
                "Institution": institution,
                "Beschreibung": description,
                "GEPRIS URL": gepris_url
            })
        except Exception as e:
            log_message(None, f"Fehler beim Parsen eines Projekts: {e}")
    return publications

# GUI-Klasse
class GeprisGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("DFG GEPRIS Publikations-Suchtool - Ultimate GUI")
        self.master.geometry("1200x800")
        self.search_results = []
        self.output_path = load_settings()
        self.pause_flag = False
        self.stop_flag = False
        self.persons = []  # Personenliste
        self.create_widgets()

    def create_widgets(self):
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab: Personen & Suche
        self.tab_person = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_person, text="Personen & Suche")
        self.create_person_tab()

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

        # Steuerungsbereich
        self.control_frame = ttk.Frame(self.master)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.create_control_buttons()

    # Personen & Suche Tab
    def create_person_tab(self):
        frame_input = ttk.LabelFrame(self.tab_person, text="Person hinzufügen/bearbeiten", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frame_input, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_name = ttk.Entry(frame_input, width=40)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_input, text="Suchbegriff:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_query = ttk.Entry(frame_input, width=40)
        self.entry_query.grid(row=1, column=1, padx=5, pady=5)

        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=2, column=0, columnspan=2, pady=5)
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
        columns = ("Name", "Suchbegriff")
        self.tree_persons = ttk.Treeview(frame_tree, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree_persons.heading(col, text=col)
            self.tree_persons.column(col, width=200 if col=="Name" else 300)
        self.tree_persons.pack(fill=tk.BOTH, expand=True)

        frame_imp_exp = ttk.Frame(self.tab_person)
        frame_imp_exp.pack(fill=tk.X, padx=10, pady=5)
        self.btn_import = ttk.Button(frame_imp_exp, text="Importieren", command=self.import_persons)
        self.btn_import.pack(side=tk.LEFT, padx=5)
        self.btn_export = ttk.Button(frame_imp_exp, text="Exportieren", command=self.export_persons)
        self.btn_export.pack(side=tk.LEFT, padx=5)

    def add_person(self):
        name = self.entry_name.get().strip()
        query = self.entry_query.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        person = {"name": name, "search_term": query}
        self.persons.append(person)
        self.update_person_tree()
        self.clear_person_inputs()
        log_message(self.text_log, f"Person '{name}' hinzugefügt.")

    def edit_person(self):
        selected = self.tree_persons.selection()
        if not selected:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine Person aus.")
            return
        idx = int(selected[0])
        person = self.persons[idx]
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, person["name"])
        self.entry_query.delete(0, tk.END)
        self.entry_query.insert(0, person["search_term"])
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
        query = self.entry_query.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        self.persons[editing_person_index] = {"name": name, "search_term": query}
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
        del self.persons[idx]
        self.update_person_tree()
        self.clear_person_inputs()
        log_message(self.text_log, "Person gelöscht.")

    def update_person_tree(self):
        for item in self.tree_persons.get_children():
            self.tree_persons.delete(item)
        for i, p in enumerate(self.persons):
            self.tree_persons.insert("", tk.END, iid=str(i), values=(p["name"], p["search_term"]))

    def clear_person_inputs(self):
        self.entry_name.delete(0, tk.END)
        self.entry_query.delete(0, tk.END)

    def import_persons(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                self.persons = imported
                self.update_person_tree()
                messagebox.showinfo("Import erfolgreich", f"Personenliste aus {file_path} geladen.")
                log_message(self.text_log, "Personenliste importiert.")
            except Exception as e:
                messagebox.showerror("Import Fehler", f"Fehler beim Importieren: {e}")

    def export_persons(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.persons, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Export erfolgreich", f"Personenliste nach {file_path} exportiert.")
                log_message(self.text_log, "Personenliste exportiert.")
            except Exception as e:
                messagebox.showerror("Export Fehler", f"Fehler beim Exportieren: {e}")

    # Erweiterte Optionen Tab
    def create_options_tab(self):
        frame_opts = ttk.LabelFrame(self.tab_options, text="Suchparameter", padding=10)
        frame_opts.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_opts, text="Startdatum (yyyy-mm-dd):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_start_date = DateEntry(frame_opts, width=12, date_pattern='yyyy-mm-dd')
        self.entry_start_date.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_opts, text="Enddatum (yyyy-mm-dd):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_end_date = DateEntry(frame_opts, width=12, date_pattern='yyyy-mm-dd')
        self.entry_end_date.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(frame_opts, text="Weitere Filter (optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_filter = ttk.Entry(frame_opts, width=40)
        self.entry_filter.grid(row=1, column=1, padx=5, pady=5, columnspan=3)

        # Ausgabepfad
        frame_output = ttk.LabelFrame(self.tab_options, text="Ausgabepfad", padding=10)
        frame_output.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_output, text="Ausgabedatei:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_output_path = ttk.Entry(frame_output, width=60)
        self.entry_output_path.grid(row=0, column=1, padx=5, pady=5)
        self.btn_browse = ttk.Button(frame_output, text="Durchsuchen", command=self.select_output_path)
        self.btn_browse.grid(row=0, column=2, padx=5, pady=5)

        # Ausgabeformat
        ttk.Label(frame_output, text="Format:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.combo_format = ttk.Combobox(frame_output, values=["Excel (.xlsx)", "CSV (.csv)"])
        self.combo_format.current(0)
        self.combo_format.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Ausgabe Tab
    def create_output_tab(self):
        frame_output = ttk.LabelFrame(self.tab_output, text="Ausgabe-Einstellungen", padding=10)
        frame_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        ttk.Label(frame_output, text="Wählen Sie die Ausgabespalten:").pack(anchor="w", pady=(0,5))
        frame_checkbuttons = ttk.Frame(frame_output)
        frame_checkbuttons.pack(fill=tk.BOTH, expand=True)
        self.available_columns = settings.get("output_columns", ["Name", "Projekt Titel", "Projekt ID", "Förderjahr", "Projektleiter", "Institution", "Beschreibung", "GEPRIS URL"])
        self.output_vars = {}
        columns_per_row = 2
        for idx, col in enumerate(self.available_columns):
            var = tk.BooleanVar(value=True)
            self.output_vars[col] = var
            chk = ttk.Checkbutton(frame_checkbuttons, text=col, variable=var)
            chk.grid(row=idx // columns_per_row, column=idx % columns_per_row, sticky="w", padx=5, pady=2)

    # Suchergebnisse Tab
    def create_results_tab(self):
        frame_results = ttk.LabelFrame(self.tab_results, text="Suchergebnisse", padding=10)
        frame_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = settings.get("output_columns", ["Name", "Projekt Titel", "Projekt ID", "Förderjahr", "Projektleiter", "Institution", "Beschreibung", "GEPRIS URL"])
        self.tree_results = ttk.Treeview(frame_results, columns=cols, show="headings")
        for col in cols:
            self.tree_results.heading(col, text=col)
            self.tree_results.column(col, width=120, anchor="w")
        vsb = ttk.Scrollbar(frame_results, orient="vertical", command=self.tree_results.yview)
        self.tree_results.configure(yscrollcommand=vsb.set)
        self.tree_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.btn_export_results = ttk.Button(self.tab_results, text="Ergebnisse exportieren", command=self.export_results)
        self.btn_export_results.pack(pady=5)

    # Log Tab
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

    # Einstellungen Tab
    def create_settings_tab(self):
        frame_settings = ttk.LabelFrame(self.tab_settings, text="Einstellungen", padding=10)
        frame_settings.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_settings, text="Ausgabespalten (Komma-getrennt):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_output_columns = ttk.Entry(frame_settings, width=60)
        self.entry_output_columns.grid(row=0, column=1, padx=5, pady=5)
        current_columns = settings.get("output_columns", [])
        self.entry_output_columns.insert(0, ", ".join(current_columns))
        self.btn_save_settings = ttk.Button(frame_settings, text="Einstellungen speichern", command=self.save_gui_settings)
        self.btn_save_settings.grid(row=1, column=0, columnspan=2, pady=10)

    def save_gui_settings(self):
        new_output_columns = [col.strip() for col in self.entry_output_columns.get().split(",") if col.strip()]
        current_output = load_settings()
        save_settings(current_output, settings.get("unique_filenames", False), new_output_columns)
        messagebox.showinfo("Einstellungen", "Die Einstellungen wurden erfolgreich gespeichert.")
        log_message(self.text_log, "Einstellungen aktualisiert.")

    # Analyse Tab
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
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(["Ergebnisse"], [len(self.search_results)], color="skyblue")
        ax.set_title("Anzahl der Ergebnisse")
        plt.tight_layout()
        if hasattr(self, "chart_canvas"):
            self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.tab_analysis)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        log_message(self.text_log, "Diagramm aktualisiert.")

    # Menüleiste
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
        messagebox.showinfo("Über", "DFG GEPRIS Publikations-Suchtool\nVersion 1.0\nErstellt von [Ihr Name]")

    # Steuerungsbuttons
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

    # Suchvorgang
    def start_search(self):
        if not self.persons:
            messagebox.showwarning("Keine Personen", "Bitte fügen Sie mindestens eine Person hinzu.")
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
        t = threading.Thread(target=self.run_search)
        t.start()

    def run_search(self):
        total = len(self.persons)
        for idx, person in enumerate(self.persons):
            if self.stop_flag:
                log_message(self.text_log, "Suche abgebrochen.")
                break
            while self.pause_flag:
                time.sleep(0.5)
            base_query = person["search_term"]
            additional_filter = self.entry_filter.get().strip()
            final_query = f"({base_query}) AND ({additional_filter})" if additional_filter else base_query
            start_date = self.entry_start_date.get().strip()
            end_date = self.entry_end_date.get().strip()
            if start_date and end_date:
                final_query += f" AND (Datum:[{start_date} TO {end_date}])"
            log_message(self.text_log, f"Suche für {person['name']} mit Query: {final_query}")
            results = search_gepris(final_query, person["name"], max_results=100)
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

    def update_status(self, current_person, progress, results_count, remaining):
        status_text = f"Verarbeite: {current_person} | Fortschritt: {progress:.1f}% | Ergebnisse: {results_count} | Verbleibende Zeit: {remaining:.0f} s"
        self.status_label.config(text=status_text)

    def update_results_tree(self):
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
        for i, result in enumerate(self.search_results):
            values = tuple(result.get(col, "") for col in settings.get("output_columns", []))
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

if __name__ == "__main__":
    root = tk.Tk()
    app = GeprisGUI(root)
    root.mainloop()
