#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PubMed Publikations-Suchtool – Ultimate GUI
Erstellt von Maximilian Paasch

Dieses Skript bietet eine umfangreiche GUI-Anwendung zur Suche in der PubMed-Datenbank.
Es umfasst Funktionen zur Personenverwaltung, erweiterte Suchoptionen, Ergebnisanzeige,
Logging, Analyse, Einstellungen sowie erweiterte Funktionen wie asynchrone API-Anfragen
und robustes Fehlerhandling.

Hinweis: Dieser Code umfasst mittlerweile über 1100 Zeilen und wurde um interaktive Datumsauswahl
sowie eine Echtzeit-Statusleiste erweitert.
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
from time import sleep
from functools import lru_cache
import threading
import time
import asyncio
import aiohttp
import logging
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Neuer Import für Datumsauswahl
from tkcalendar import DateEntry

# Globaler API-Key (bitte sicher aufbewahren!)
API_KEY = "fd409653aa8c7f336421d20a0e862459b507"

# Konfigurationsdatei
config_file = "pubmed_config_extended.json"

# Globale Variablen
persons = []                # Liste der Personen (jeder Eintrag ist ein Dictionary)
search_results = []         # Gesammelte Suchergebnisse
editing_person_index = None
settings = {}               # Einstellungen aus der Config-Datei
global_log = []             # Globaler Log (Liste von Logeinträgen)

##############################
# Einstellungen laden und speichern
##############################
def load_settings():
    global settings
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "output_columns": ["Name", "Titel", "Veröffentlichungsjahr", "Autoren", "Zitationsanzahl"]
        }
        save_settings(settings["output_path"], settings["person_list_path"],
                      settings["unique_filenames"], settings["output_columns"])
    return settings.get("output_path", "./output"), settings.get("person_list_path", "./person_lists")

def save_settings(output_path, person_list_path, unique_filenames, output_columns):
    settings["output_path"] = output_path
    settings["person_list_path"] = person_list_path
    settings["unique_filenames"] = unique_filenames
    settings["output_columns"] = output_columns
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

##############################
# Logging-Funktionen
##############################
def log_message(log_widget, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    global_log.append(full_msg)
    log_widget.config(state="normal")
    log_widget.insert(tk.END, full_msg)
    log_widget.see(tk.END)
    log_widget.config(state="disabled")

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
# Caching für Zitationsanzahl
##############################
@lru_cache(maxsize=128)
def get_citation_count(pmid):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    elink_url = base_url + "elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "linkname": "pubmed_pubmed_citedin",
        "id": pmid,
        "retmode": "xml",
        "api_key": API_KEY
    }
    max_retries = 3
    delay = 0.5
    for attempt in range(max_retries):
        try:
            response = requests.get(elink_url, params=params)
            response.raise_for_status()
            xml = ET.fromstring(response.content)
            count = len(xml.findall(".//LinkSetDb/Link/Id"))
            return count
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"429 Error for PMID {pmid}. Warte {delay} Sekunden...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"Fehler beim Abrufen der Zitationsanzahl für PMID {pmid}: {e}")
                return "Fehler"
        except ET.ParseError as e:
            print(f"Parse-Fehler für PMID {pmid}: {e}")
            return "Fehler XML"
    print(f"Maximale Wiederholungen für PMID {pmid} überschritten.")
    return "Fehler 429"

##############################
# PubMed Suchfunktion (synchron)
##############################
def search_pubmed(query, name, max_results=1000):
    """
    Sucht in PubMed nach Publikationen und extrahiert detaillierte Informationen.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_url = base_url + "esearch.fcgi"
    efetch_url = base_url + "efetch.fcgi"
    
    esearch_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "api_key": API_KEY
    }
    
    try:
        response = requests.get(esearch_url, params=esearch_params)
        response.raise_for_status()
        esearch_xml = ET.fromstring(response.content)
        id_list = [node.text for node in esearch_xml.findall(".//Id")]
        if not id_list:
            print(f"Keine Publikationen für {query} gefunden.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der Suche für {query}: {e}")
        return []
    
    efetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        "api_key": API_KEY
    }
    try:
        response = requests.get(efetch_url, params=efetch_params)
        response.raise_for_status()
        efetch_xml = ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Daten für {query}: {e}")
        return []
    
    publications = []
    for article in efetch_xml.findall(".//PubmedArticle"):
        try:
            title_el = article.find(".//ArticleTitle")
            title = title_el.text if title_el is not None else "Kein Titel"
            pub_date_el = article.find(".//PubDate")
            year = pub_date_el.find("Year").text if pub_date_el is not None and pub_date_el.find("Year") is not None else "Kein Jahr"
            month_el = pub_date_el.find("Month") if pub_date_el is not None else None
            month_raw = month_el.text if month_el is not None else ""
            try:
                month_numeric = datetime.strptime(month_raw, "%b").strftime("%m")
            except:
                try:
                    month_numeric = datetime.strptime(month_raw, "%B").strftime("%m")
                except:
                    try:
                        month_numeric = str(int(month_raw)).zfill(2)
                    except:
                        month_numeric = month_raw
            authors = []
            for author in article.findall(".//Author"):
                ln = author.find(".//LastName")
                fn = author.find(".//ForeName")
                if ln is not None and fn is not None:
                    authors.append(f"{fn.text} {ln.text}")
                else:
                    authors.append("Kein Name")
            authors_str = ", ".join(authors)
            pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
            pub_types_str = ", ".join(pub_types) if pub_types else "Keine Artikeltypen"
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else "Keine PMID"
            pmcid_el = article.find('.//ArticleId[@IdType="pmc"]')
            pmcid = pmcid_el.text if pmcid_el is not None else "Keine PMCID"
            doi_el = article.find('.//ArticleId[@IdType="doi"]')
            doi = doi_el.text if doi_el is not None else "Keine DOI"
            doi_url = f"https://doi.org/{doi}" if doi != "Keine DOI" else "Keine DOI URL"
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "Keine PMID" else "Keine PubMed URL"
            affils = [aff.text for aff in article.findall(".//AffiliationInfo/Affiliation") if aff.text]
            affils_str = "\n".join(affils) if affils else "Keine Affiliationsdaten"
            
            citation_count = get_citation_count(pmid) if pmid != "Keine PMID" else "N/A"
            
            publications.append({
                "Name": name,
                "Titel": title,
                "Veröffentlichungsjahr": year,
                "Veröffentlichungsmonat": month_numeric,
                "Autoren": authors_str,
                "Publikationstypen": pub_types_str,
                "Affiliations": affils_str,
                "PubMed URL": pubmed_url,
                "DOI URL": doi_url,
                "PubMed-ID": pmid,
                "PMCID": pmcid,
                "DOI": doi,
                "Zitationsanzahl": citation_count
            })
        except Exception as e:
            print(f"Fehler beim Parsen einer Publikation für {query}: {e}")
    return publications

##############################
# GUI-Klasse
##############################
class PubMedGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("PubMed Publikations-Suchtool - Ultimate GUI")
        self.master.geometry("1200x800")
        self.pause_flag = False
        self.stop_flag = False
        self.search_results = []
        self.output_path = ""
        self.create_widgets()
        # Lade initiale Einstellungen
        output_path, _ = load_settings()
        self.output_path = output_path

    def create_widgets(self):
        # Erstelle Notebook (Tabs)
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
        
        # Erstelle Menüleiste
        self.create_menu_bar()
        
        # Steuerungsbereich unten
        self.control_frame = ttk.Frame(self.master)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.create_control_buttons()

    ##############################
    # Tab "Personen & Suche"
    ##############################
    def create_person_tab(self):
        frame_input = ttk.LabelFrame(self.tab_person, text="Person hinzufügen/bearbeiten", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_input, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_name = ttk.Entry(frame_input, width=40)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Suchbegriff:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_query = ttk.Entry(frame_input, width=40)
        self.entry_query.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Suchfeld:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.search_field_values = ["Alle Felder", "Titel/Abstract", "Autor", "Journal"]
        self.combobox_field = ttk.Combobox(frame_input, values=self.search_field_values, state="readonly", width=15)
        self.combobox_field.set(self.search_field_values[0])
        self.combobox_field.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Zusätzliche Suchbegriffe:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_additional = ttk.Entry(frame_input, width=40)
        self.entry_additional.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="DOI Suche (optional):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_doi = ttk.Entry(frame_input, width=40)
        self.entry_doi.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Publikationstyp (optional):").grid(row=3, column=2, sticky="w", padx=5, pady=5)
        self.pub_type_values = ["Alle", "Review", "Clinical Trial", "Meta-Analysis", "Randomized Controlled Trial"]
        self.combobox_pub_type = ttk.Combobox(frame_input, values=self.pub_type_values, state="readonly", width=15)
        self.combobox_pub_type.set(self.pub_type_values[0])
        self.combobox_pub_type.grid(row=3, column=3, padx=5, pady=5)
        
        frame_buttons = ttk.Frame(frame_input)
        frame_buttons.grid(row=4, column=0, columnspan=4, pady=5)
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
        columns = ("Name", "Suchbegriff", "Suchfeld")
        self.tree_persons = ttk.Treeview(frame_tree, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree_persons.heading(col, text=col)
            if col == "Name":
                self.tree_persons.column(col, width=200)
            elif col == "Suchbegriff":
                self.tree_persons.column(col, width=300)
            else:
                self.tree_persons.column(col, width=150)
        self.tree_persons.pack(fill=tk.BOTH, expand=True)
        
        frame_imp_exp = ttk.Frame(self.tab_person)
        frame_imp_exp.pack(fill=tk.X, padx=10, pady=5)
        self.btn_import = ttk.Button(frame_imp_exp, text="Importieren", command=self.import_persons)
        self.btn_import.pack(side=tk.LEFT, padx=5)
        self.btn_export = ttk.Button(frame_imp_exp, text="Exportieren", command=self.export_persons)
        self.btn_export.pack(side=tk.LEFT, padx=5)

    ##############################
    # Tab "Erweiterte Optionen" (mit DateEntry statt Textfeldern)
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
        
        ttk.Label(frame_opts, text="Ausgabeformat:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.combo_format = ttk.Combobox(frame_opts, values=["Excel (.xlsx)", "CSV (.csv)"], state="readonly", width=15)
        self.combo_format.current(0)
        self.combo_format.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame_opts, text="Ausgabepfad:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_output_path = ttk.Entry(frame_opts, width=40)
        self.entry_output_path.grid(row=2, column=1, padx=5, pady=5, columnspan=2)
        self.btn_browse = ttk.Button(frame_opts, text="Durchsuchen", command=self.select_output_path)
        self.btn_browse.grid(row=2, column=3, padx=5, pady=5)
        
        ttk.Label(frame_opts, text="Sprache (optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_language = ttk.Entry(frame_opts, width=10)
        self.entry_language.grid(row=3, column=1, padx=5, pady=5)

    ##############################
    # Tab "Ausgabe" – Erweiterte Ausgabeoptionen per Checkbuttons
    ##############################
    def create_output_tab(self):
        frame_output = ttk.LabelFrame(self.tab_output, text="Ausgabe-Einstellungen", padding=10)
        frame_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(frame_output, text="Wählen Sie die Ausgabespalten:").pack(anchor="w", pady=(0,5))
        
        # Neuer Untercontainer, in dem grid genutzt wird
        frame_checkbuttons = ttk.Frame(frame_output)
        frame_checkbuttons.pack(fill=tk.BOTH, expand=True)
        
        self.available_columns = [
            "Name", "Titel", "Veröffentlichungsjahr", "Veröffentlichungsmonat", "Autoren",
            "Publikationstypen", "Affiliations", "PubMed URL", "DOI URL", "PubMed-ID",
            "PMCID", "DOI", "Zitationsanzahl"
        ]
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
        cols = ("Name", "Titel", "Veröffentlichungsjahr", "Veröffentlichungsmonat", "Autoren",
                "Publikationstypen", "Affiliations", "PubMed URL", "DOI URL", "PubMed-ID", "PMCID", "DOI", "Zitationsanzahl")
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
        self.entry_api_key.insert(0, API_KEY)
        
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
        current_output, current_person_list = load_settings()
        save_settings(current_output, current_person_list, settings.get("unique_filenames", False), new_output_columns)
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
        self.btn_show_chart = ttk.Button(frame_analysis_buttons, text="Diagramm anzeigen", command=self.display_publication_type_chart)
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

    def display_publication_type_chart(self):
        pub_type_counts = {}
        for result in self.search_results:
            types_str = result.get("Publikationstypen", "Keine Artikeltypen")
            types = [t.strip() for t in types_str.split(",") if t.strip()]
            if not types:
                types = ["Keine Artikeltypen"]
            for t in types:
                pub_type_counts[t] = pub_type_counts.get(t, 0) + 1
        if not pub_type_counts:
            messagebox.showinfo("Analyse", "Keine Daten für die Analyse vorhanden.")
            return
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(pub_type_counts.keys(), pub_type_counts.values(), color="skyblue")
        ax.set_title("Verteilung der Publikationstypen")
        ax.set_xlabel("Publikationstyp")
        ax.set_ylabel("Anzahl")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        if hasattr(self, "chart_canvas"):
            self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.tab_analysis)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        log_message(self.text_log, "Diagramm zur Publikationstyp-Verteilung aktualisiert.")

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
        # Neue Statusleiste
        self.status_label = ttk.Label(self.control_frame, text="Status: Idle")
        self.status_label.pack(fill=tk.X, padx=5, pady=(5,0))

    ##############################
    # Methoden zur Personenverwaltung
    ##############################
    def add_person(self):
        name = self.entry_name.get().strip()
        query = self.entry_query.get().strip()
        additional = self.entry_additional.get().strip()
        search_field = self.combobox_field.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        person = {"name": name, "search_term": query, "additional_search": additional, "search_field": search_field}
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
        self.entry_query.delete(0, tk.END)
        self.entry_query.insert(0, person["search_term"])
        self.entry_additional.delete(0, tk.END)
        self.entry_additional.insert(0, person.get("additional_search", ""))
        self.combobox_field.set(person.get("search_field", self.search_field_values[0]))
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
        additional = self.entry_additional.get().strip()
        search_field = self.combobox_field.get().strip()
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
        persons[editing_person_index] = {"name": name, "search_term": query, "additional_search": additional, "search_field": search_field}
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
            self.tree_persons.insert("", tk.END, iid=str(i), values=(p["name"], p["search_term"], p.get("search_field", self.search_field_values[0])))
    
    def clear_person_inputs(self):
        self.entry_name.delete(0, tk.END)
        self.entry_query.delete(0, tk.END)
        self.entry_additional.delete(0, tk.END)
        self.combobox_field.set(self.search_field_values[0])
    
    def import_persons(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
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
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Dateien", "*.json"), ("Alle Dateien", "*.*")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(persons, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Export erfolgreich", f"Personenliste nach {file_path} exportiert.")
                log_message(self.text_log, "Personenliste exportiert.")
            except Exception as e:
                messagebox.showerror("Export Fehler", f"Fehler beim Exportieren: {e}")
    
    ##############################
    # Steuerung des Suchvorgangs (Thread) inkl. Echtzeit-Statusupdates
    ##############################
    def start_search(self):
        if not persons:
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
        # Speichere den Startzeitpunkt für die Zeitschätzung
        self.search_start_time = time.time()
        t = threading.Thread(target=self.run_search)
        t.start()
    
    def run_search(self):
        total = len(persons)
        for idx, person in enumerate(persons):
            if self.stop_flag:
                log_message(self.text_log, "Suche abgebrochen.")
                break
            while self.pause_flag:
                time.sleep(0.5)
            base_query = person["search_term"]
            additional = person.get("additional_search", "")
            if additional:
                final_query = f"({base_query}) AND ({additional})"
            else:
                final_query = base_query
            # Datumsauswahl aus DateEntry-Feldern (Format: yyyy-mm-dd -> yyyy/mm/dd)
            start_date = self.entry_start_date.get().strip() or None
            end_date = self.entry_end_date.get().strip() or None
            if start_date and end_date:
                start_date_fmt = start_date.replace("-", "/")
                end_date_fmt = end_date.replace("-", "/")
                final_query += f" AND (\"{start_date_fmt}\"[Date - Publication] : \"{end_date_fmt}\"[Date - Publication])"
            # Entfernt: die Zeile, die 'search_field' anhängt, da dies ungültige Queries erzeugt.
            pub_type = None
            if self.combobox_pub_type.get() != "Alle":
                pub_type = self.combobox_pub_type.get().strip()
            lang = self.entry_language.get().strip() or None
            if pub_type:
                final_query += f" AND {pub_type}"
            if lang:
                final_query += f" AND {lang}[Language]"
            log_message(self.text_log, f"Suche für {person['name']} mit Query: {final_query}")
            results = search_pubmed(final_query, person["name"], max_results=1000)
            self.search_results.extend(results)
            progress = ((idx + 1) / total) * 100
            self.master.after(0, self.progress_var.set, progress)
            self.master.after(0, self.update_results_tree)
            # Berechne verbleibende Zeit
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
        status_text = (f"Verarbeite: {current_person} | "
                       f"Fortschritt: {progress:.1f}% | "
                       f"Ergebnisse: {results_count} | "
                       f"Verbleibende Zeit: {remaining:.0f} s")
        self.status_label.config(text=status_text)
    
    ##############################
    # Ergebnisse aktualisieren und exportieren
    ##############################
    def update_results_tree(self):
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
        for i, result in enumerate(self.search_results):
            values = (
                result.get("Name", ""),
                result.get("Titel", ""),
                result.get("Veröffentlichungsjahr", ""),
                result.get("Veröffentlichungsmonat", ""),
                result.get("Autoren", ""),
                result.get("Publikationstypen", ""),
                result.get("Affiliations", ""),
                result.get("PubMed URL", ""),
                result.get("DOI URL", ""),
                result.get("PubMed-ID", ""),
                result.get("PMCID", ""),
                result.get("DOI", ""),
                result.get("Zitationsanzahl", "")
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
            current_output, current_person_list = load_settings()
            save_settings(os.path.dirname(file_path), current_person_list, settings.get("unique_filenames", False), settings.get("output_columns", []))
            self.output_path = os.path.dirname(file_path)
            log_message(self.text_log, f"Ausgabepfad gesetzt auf: {file_path}")
    
    ##############################
    # Erweiterte Funktionen (Asynchron, Logging, Reset, robust_get)
    ##############################
    async def async_get(self, url, params):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.text()
    
    async def async_search_pubmed(self, query, name, max_results=1000):
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        esearch_url = base_url + "esearch.fcgi"
        efetch_url = base_url + "efetch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "api_key": API_KEY
        }
        try:
            esearch_response_text = await self.async_get(esearch_url, esearch_params)
            esearch_xml = ET.fromstring(esearch_response_text)
            id_list = [node.text for node in esearch_xml.findall('.//Id')]
            if not id_list:
                logging.info(f"Keine Publikationen für {query} gefunden.")
                return []
        except Exception as e:
            logging.error(f"Asynchrone ESearch-Fehler für {query}: {e}")
            return []
    
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "api_key": API_KEY
        }
        try:
            efetch_response_text = await self.async_get(efetch_url, efetch_params)
            efetch_xml = ET.fromstring(efetch_response_text)
        except Exception as e:
            logging.error(f"Asynchrone EFetch-Fehler für {query}: {e}")
            return []
    
        pubs = []
        for article in efetch_xml.findall(".//PubmedArticle"):
            try:
                title_el = article.find('.//ArticleTitle')
                title = title_el.text if title_el is not None else "Kein Titel"
                pub_date_el = article.find('.//PubDate')
                year = pub_date_el.find('Year').text if pub_date_el is not None and pub_date_el.find('Year') is not None else "Keine Jahr"
                month_el = pub_date_el.find('Month') if pub_date_el is not None else None
                month_raw = month_el.text if month_el is not None else ""
                month_numeric = month_raw if month_raw.isdigit() else ""
                authors = []
                for author in article.findall('.//Author'):
                    ln = author.find('.//LastName')
                    fn = author.find('.//ForeName')
                    if ln is not None and fn is not None:
                        authors.append(f"{fn.text} {ln.text}")
                    else:
                        authors.append("Kein Name")
                authors_str = ", ".join(authors)
                affils = [aff.text for aff in article.findall('.//AffiliationInfo/Affiliation') if aff.text]
                affils_str = "\n".join(affils) if affils else "Keine Affiliationsdaten"
                pmid = article.find('.//PMID').text if article.find('.//PMID') is not None else "Keine PMID"
                doi_el = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_el.text if doi_el is not None else "Keine DOI"
                doi_url = f"https://doi.org/{doi}" if doi != "Keine DOI" else "Keine DOI URL"
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "Keine PMID" else "Keine PubMed URL"
                citation_count = get_citation_count(pmid) if pmid != "Keine PMID" else "N/A"
                pubs.append({
                    "Name": name,
                    "Titel": title,
                    "Veröffentlichungsjahr": year,
                    "Veröffentlichungsmonat": month_numeric,
                    "Autoren": authors_str,
                    "Affiliations": affils_str,
                    "PubMed URL": pubmed_url,
                    "DOI URL": doi_url,
                    "PubMed-ID": pmid,
                    "DOI": doi,
                    "Zitationsanzahl": citation_count
                })
            except Exception as e:
                logging.error(f"Fehler beim asynchronen Parsen für {query}: {e}")
        return pubs

    def export_log_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")])
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Logeintrag"])
                for entry in global_log:
                    if entry.startswith("[") and "]" in entry:
                        timestamp, message = entry.split("]", 1)
                        writer.writerow([timestamp.strip("["), message.strip()])
                    else:
                        writer.writerow(["", entry.strip()])
            messagebox.showinfo("Log exportiert", f"Log-Daten wurden als CSV in {file_path} gespeichert.")
        except Exception as e:
            messagebox.showerror("Export Fehler", f"Fehler beim Exportieren des Logs als CSV: {e}")

    def reset_search(self):
        self.search_results = []
        self.update_results_tree()
        self.progress_var.set(0)
        log_message(self.text_log, "Suchergebnisse und Status wurden zurückgesetzt.")

    def robust_get(self, url, params, max_retries=3, initial_delay=0.5):
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                log_message(self.text_log, f"Fehler bei Anfrage an {url}: {e} (Versuch {attempt+1} von {max_retries})")
                time.sleep(delay)
                delay *= 2
        log_message(self.text_log, f"Alle Versuche für {url} fehlgeschlagen.")
        return None

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
        messagebox.showinfo("Über", "PubMed Publikations-Suchtool\nVersion 1.0\nErstellt von Maximilian Paasch")

##############################
# Ende der Klasse PubMedGUI
##############################

def main():
    root = tk.Tk()
    app = PubMedGUI(root)
    app.progress_var = tk.DoubleVar()
    root.mainloop()

if __name__ == "__main__":
    main()
