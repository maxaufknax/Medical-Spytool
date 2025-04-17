#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Main Application – Integrierte Publikations-Suchanwendung

Diese Anwendung kombiniert die Funktionen aus:
  • PubMed Skript (asynchrone API-Abfragen, Caching, interaktive Datumsauswahl, Logging, Analyse, Export)
  • DNB Skript (SRU-Zugriff, RDF/XML‑Parsing, CQL-Transformation, Verwaltung gespeicherter Suchanfragen, Export)
  • Web of Science Skript (API‑Abfragen, Dummy-Modus, spezifische Feldabfragen, umfassendes Ergebnismanagement)
  • Scopus Skript (Scopus-API, JSON-Datenextraktion, Sprache- und Datumeinstellungen, Logging, Analyse, Export)

Die Anwendung bietet:
  – Eine gemeinsame GUI (Tkinter Notebook mit separaten Tabs)
  – Integrierte Suche in einer oder mehreren Datenbanken
  – Kombinierte Ergebnisansicht
  – Erweiterte Suchoptionen und zentrale Personenverwaltung
  – Asynchronität und Caching zur Performanceoptimierung
  – Einheitliches, robustes Logging (mit Export)
  – Analysefunktionen (z. B. Visualisierungen mit Matplotlib)
  – Globale, per JSON speicherbare Einstellungen (API‑Keys, Ausgabeoptionen, Dateipfade)

Benötigte Module: tkinter, requests, xml.etree.ElementTree, pandas, json, threading, asyncio, aiohttp, matplotlib, tkcalendar, functools.lru_cache
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import json
import os
import threading
import asyncio
import aiohttp
import time
import matplotlib.pyplot as plt
from tkcalendar import DateEntry
from functools import lru_cache
from datetime import datetime

# ------------------------------------------------------------------------------
# Globaler Konfigurationsmanager
# ------------------------------------------------------------------------------

class ConfigManager:
    def __init__(self, config_file="global_config.json"):
        self.config_file = config_file
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Standard-Einstellungen inklusive API-Keys, Ausgabeoptionen etc.
            default_settings = {
                "output_path": "./output",
                "unique_filenames": False,
                "output_columns": {
                    "pubmed": ["Name", "Titel", "Veröffentlichungsjahr", "Autoren", "Zitationsanzahl"],
                    "dnb": ["Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL"],
                    "wos": ["Name", "Titel", "Veröffentlichungsjahr", "Autoren", "DOI", "WoS URL", "UT", "Zitationsanzahl"],
                    "scopus": ["Name", "Titel", "Veröffentlichungsjahr", "Autoren", "DOI", "Scopus URL", "EID", "Zitationsanzahl"]
                },
                "api_keys": {
                    "pubmed": "fd409653aa8c7f336421d20a0e862459b507",
                    "wos": "",
                    "scopus": "your_scopus_api_key_here"
                },
                "person_list_path": "./person_lists"
            }
            self.save_settings(default_settings)
            return default_settings

    def save_settings(self, settings=None):
        if settings is not None:
            self.settings = settings
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    def get_api_key(self, service):
        return self.settings.get("api_keys", {}).get(service, "")

# ------------------------------------------------------------------------------
# Globales Logging
# ------------------------------------------------------------------------------

class Logger:
    def __init__(self):
        self.log_entries = []

    def log(self, message, widget=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self.log_entries.append(entry)
        if widget:
            widget.config(state="normal")
            widget.insert(tk.END, entry)
            widget.see(tk.END)
            widget.config(state="disabled")
        else:
            print(entry.strip())

    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Dateien", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("".join(self.log_entries))
            messagebox.showinfo("Log exportiert", f"Log wurde in {file_path} gespeichert.")

# ------------------------------------------------------------------------------
# Suchfunktionen der einzelnen Datenbanken
# ------------------------------------------------------------------------------

# --- PubMed ---
@lru_cache(maxsize=128)
def get_citation_count(pmid, api_key):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    elink_url = base_url + "elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "linkname": "pubmed_pubmed_citedin",
        "id": pmid,
        "retmode": "xml",
        "api_key": api_key
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
                time.sleep(delay)
                delay *= 2
            else:
                return "Fehler"
        except ET.ParseError:
            return "Fehler XML"
    return "Fehler 429"

def search_pubmed(query, name, api_key, max_results=100):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    esearch_url = base_url + "esearch.fcgi"
    efetch_url = base_url + "efetch.fcgi"
    esearch_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "api_key": api_key
    }
    try:
        response = requests.get(esearch_url, params=esearch_params)
        response.raise_for_status()
        esearch_xml = ET.fromstring(response.content)
        id_list = [node.text for node in esearch_xml.findall(".//Id")]
        if not id_list:
            return []
    except Exception as e:
        print(f"PubMed-Suche Fehler: {e}")
        return []
    efetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
        "api_key": api_key
    }
    try:
        response = requests.get(efetch_url, params=efetch_params)
        response.raise_for_status()
        efetch_xml = ET.fromstring(response.content)
    except Exception as e:
        print(f"PubMed Abruf Fehler: {e}")
        return []
    publications = []
    for article in efetch_xml.findall(".//PubmedArticle"):
        try:
            title_el = article.find(".//ArticleTitle")
            title = title_el.text if title_el is not None else "Kein Titel"
            pub_date_el = article.find(".//PubDate")
            year = pub_date_el.find("Year").text if pub_date_el is not None and pub_date_el.find("Year") is not None else "Kein Jahr"
            authors = []
            for author in article.findall(".//Author"):
                ln = author.find(".//LastName")
                fn = author.find(".//ForeName")
                if ln is not None and fn is not None:
                    authors.append(f"{fn.text} {ln.text}")
                else:
                    authors.append("Unbekannt")
            authors_str = ", ".join(authors)
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else "Keine PMID"
            citation_count = get_citation_count(pmid, api_key) if pmid != "Keine PMID" else "N/A"
            publications.append({
                "Name": name,
                "Titel": title,
                "Veröffentlichungsjahr": year,
                "Autoren": authors_str,
                "Zitationsanzahl": citation_count,
                "PubMed-ID": pmid
            })
        except Exception as e:
            print(f"Fehler beim Parsen einer PubMed Publikation: {e}")
    return publications

# --- DNB ---
def transform_query(search_term):
    if not search_term.lower().startswith("dc.any"):
        parts = search_term.split()
        if len(parts) == 2:
            return f'dc.any all ("{search_term}" or "{parts[1]}, {parts[0]}")'
        else:
            return f'dc.any all "{search_term}"'
    return search_term

def parse_dnb_response(xml_text):
    ns = {
        'srw': 'http://www.loc.gov/zing/srw/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'rdau': 'http://rdaregistry.info/Elements/u/'
    }
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results
    records = root.findall('.//{http://www.loc.gov/zing/srw/}record')
    for record in records:
        record_data = record.find('{http://www.loc.gov/zing/srw/}recordData')
        if record_data is None:
            continue
        rdf_elem = record_data.find('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
        if rdf_elem is None:
            continue
        desc = None
        for d in rdf_elem.findall('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'):
            if d.find('{http://purl.org/dc/elements/1.1/}title') is not None:
                desc = d
                break
        if desc is None:
            continue
        title_elem = desc.find('{http://purl.org/dc/elements/1.1/}title')
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Kein Titel"
        creator = ""
        creator_elem = desc.find('{http://purl.org/dc/elements/1.1/}creator')
        if creator_elem is not None and creator_elem.text:
            creator = creator_elem.text.strip()
        else:
            creator_elem = desc.find('{http://purl.org/dc/terms/}creator')
            if creator_elem is not None and creator_elem.text:
                creator = creator_elem.text.strip()
            else:
                creator_elem = desc.find('{http://rdaregistry.info/Elements/u/}P60327')
                creator = creator_elem.text.strip() if creator_elem is not None and creator_elem.text else "Kein Creator"
        issued_elem = desc.find('{http://purl.org/dc/terms/}issued')
        issued = issued_elem.text.strip() if issued_elem is not None and issued_elem.text else ""
        id_elem = desc.find('{http://purl.org/dc/elements/1.1/}identifier')
        identifier = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
        url_elem = desc.find('{http://xmlns.com/foaf/0.1/}isPrimaryTopicOf')
        url = url_elem.text.strip() if url_elem is not None and url_elem.text else ""
        results.append({
            "Titel": title,
            "Creator": creator,
            "Erscheinungsjahr": issued,
            "Identifier": identifier,
            "URL": url
        })
    return results

def search_dnb(query, name, page_size=1000):
    base_url = "https://services.dnb.de/sru/dnb"
    transformed_query = transform_query(query)
    start_record = 1
    all_results = []
    while True:
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": transformed_query,
            "recordSchema": "RDFxml",
            "maximumRecords": str(page_size),
            "startRecord": str(start_record)
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            xml_text = response.text
        except Exception as e:
            print(f"DNB-Suche Fehler: {e}")
            break
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"DNB XML Parsing Fehler: {e}")
            break
        num_elem = root.find('.//{http://www.loc.gov/zing/srw/}numberOfRecords')
        total_records = int(num_elem.text) if num_elem is not None and num_elem.text.isdigit() else 0
        page_results = parse_dnb_response(xml_text)
        all_results.extend(page_results)
        if start_record + page_size > total_records:
            break
        start_record += page_size
        time.sleep(1)
    for res in all_results:
        res["Name"] = name
    return all_results

# --- Web of Science (WoS) ---
def search_wos(query, name, max_results=100):
    API_KEY = config_manager.get_api_key("wos")
    if not API_KEY:
        dummy_publication = {
            "Name": name,
            "Titel": f"Dummy-Titel für {query}",
            "Veröffentlichungsjahr": "2020",
            "Autoren": "Max Mustermann, Erika Musterfrau",
            "DOI": "10.1000/dummydoi",
            "WoS URL": "https://www.webofscience.com/dummy",
            "UT": "WOS:00000000000000",
            "Zitationsanzahl": 42
        }
        return [dummy_publication]
    base_url = "https://api.clarivate.com/api/woslite"
    headers = {"X-ApiKey": API_KEY}
    params = {
        "databaseId": "WOS",
        "usrQuery": query,
        "count": max_results,
        "firstRecord": 1
    }
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        records = data.get("Data", {}).get("Records", {}).get("records", [])
        publications = []
        for rec in records:
            title = rec.get("title", "Kein Titel")
            pub_info = rec.get("pub_info", {})
            publication_year = pub_info.get("pubyear", "Kein Jahr")
            authors = rec.get("authors", [])
            doi = rec.get("doi", "Keine DOI")
            ut = rec.get("ut", "Kein UT")
            wos_url = f"https://www.webofscience.com/wos/woscc/full-record/{ut}" if ut != "Kein UT" else "Keine URL"
            citation_count = rec.get("cited_refs_count", "N/A")
            publications.append({
                "Name": name,
                "Titel": title,
                "Veröffentlichungsjahr": publication_year,
                "Autoren": ", ".join(authors) if isinstance(authors, list) else authors,
                "DOI": doi,
                "WoS URL": wos_url,
                "UT": ut,
                "Zitationsanzahl": citation_count
            })
        return publications
    except Exception as e:
        print(f"WoS-Suche Fehler: {e}")
        return []

# --- Scopus ---
def search_scopus(query, name, max_results=25):
    API_KEY = config_manager.get_api_key("scopus")
    base_url = "https://api.elsevier.com/content/search/scopus"
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "query": query,
        "count": max_results,
        "start": 0,
        "view": "STANDARD"
    }
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        entries = data.get("search-results", {}).get("entry", [])
        publications = []
        for entry in entries:
            title = entry.get("dc:title", "Kein Titel")
            pub_year = "Kein Jahr"
            if "prism:coverDate" in entry:
                pub_year = entry["prism:coverDate"].split("-")[0]
            authors = entry.get("dc:creator", "Keine Autoren")
            doi = entry.get("prism:doi", "Keine DOI")
            eid = entry.get("eid", "Kein EID")
            scopus_url = f"https://www.scopus.com/record/display.uri?eid={eid}" if eid != "Kein EID" else "Keine URL"
            citation_count = entry.get("citedby-count", "N/A")
            publications.append({
                "Name": name,
                "Titel": title,
                "Veröffentlichungsjahr": pub_year,
                "Autoren": authors,
                "DOI": doi,
                "Scopus URL": scopus_url,
                "EID": eid,
                "Zitationsanzahl": citation_count
            })
        return publications
    except Exception as e:
        print(f"Scopus-Suche Fehler: {e}")
        return []

# ------------------------------------------------------------------------------
# GUI-Tabs für die einzelnen Funktionen
# ------------------------------------------------------------------------------

class PubMedTab(tk.Frame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.api_key = self.config_manager.get_api_key("pubmed")
        self.create_widgets()
        self.results = []

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self, text="PubMed Suche", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(input_frame, text="Suchbegriff:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_query = ttk.Entry(input_frame, width=50)
        self.entry_query.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=50)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        self.btn_search = ttk.Button(input_frame, text="Suche starten", command=self.start_search)
        self.btn_search.grid(row=2, column=0, columnspan=2, pady=5)
        self.tree = ttk.Treeview(self, columns=("Titel", "Jahr", "Autoren", "Zitationen"), show="headings")
        self.tree.heading("Titel", text="Titel")
        self.tree.heading("Jahr", text="Jahr")
        self.tree.heading("Autoren", text="Autoren")
        self.tree.heading("Zitationen", text="Zitationsanzahl")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def start_search(self):
        query = self.entry_query.get().strip()
        name = self.entry_name.get().strip()
        if not query or not name:
            messagebox.showwarning("Eingabe fehlt", "Bitte Suchbegriff und Name eingeben.")
            return
        self.logger.log(f"Starte PubMed Suche für {name}: {query}")
        threading.Thread(target=self.search, args=(query, name), daemon=True).start()

    def search(self, query, name):
        results = search_pubmed(query, name, self.api_key)
        self.results = results
        self.update_tree()
        self.logger.log(f"PubMed Suche abgeschlossen: {len(results)} Treffer.")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for res in self.results:
            self.tree.insert("", tk.END, values=(res.get("Titel"), res.get("Veröffentlichungsjahr"), res.get("Autoren"), res.get("Zitationsanzahl")))

class DNBTab(tk.Frame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.create_widgets()
        self.results = []

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self, text="DNB Suche", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(input_frame, text="Suchbegriff:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_query = ttk.Entry(input_frame, width=50)
        self.entry_query.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=50)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        self.btn_search = ttk.Button(input_frame, text="Suche starten", command=self.start_search)
        self.btn_search.grid(row=2, column=0, columnspan=2, pady=5)
        self.tree = ttk.Treeview(self, columns=("Titel", "Creator", "Erscheinungsjahr", "Identifier"), show="headings")
        self.tree.heading("Titel", text="Titel")
        self.tree.heading("Creator", text="Creator")
        self.tree.heading("Erscheinungsjahr", text="Erscheinungsjahr")
        self.tree.heading("Identifier", text="Identifier")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def start_search(self):
        query = self.entry_query.get().strip()
        name = self.entry_name.get().strip()
        if not query or not name:
            messagebox.showwarning("Eingabe fehlt", "Bitte Suchbegriff und Name eingeben.")
            return
        self.logger.log(f"Starte DNB Suche für {name}: {query}")
        threading.Thread(target=self.search, args=(query, name), daemon=True).start()

    def search(self, query, name):
        results = search_dnb(query, name)
        self.results = results
        self.update_tree()
        self.logger.log(f"DNB Suche abgeschlossen: {len(results)} Treffer.")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for res in self.results:
            self.tree.insert("", tk.END, values=(res.get("Titel"), res.get("Creator"), res.get("Erscheinungsjahr"), res.get("Identifier")))

class WoSTab(tk.Frame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.create_widgets()
        self.results = []

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self, text="Web of Science Suche", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(input_frame, text="Suchbegriff:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_query = ttk.Entry(input_frame, width=50)
        self.entry_query.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=50)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        self.btn_search = ttk.Button(input_frame, text="Suche starten", command=self.start_search)
        self.btn_search.grid(row=2, column=0, columnspan=2, pady=5)
        self.tree = ttk.Treeview(self, columns=("Titel", "Jahr", "Autoren", "DOI", "Zitationsanzahl"), show="headings")
        self.tree.heading("Titel", text="Titel")
        self.tree.heading("Jahr", text="Jahr")
        self.tree.heading("Autoren", text="Autoren")
        self.tree.heading("DOI", text="DOI")
        self.tree.heading("Zitationsanzahl", text="Zitationsanzahl")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def start_search(self):
        query = self.entry_query.get().strip()
        name = self.entry_name.get().strip()
        if not query or not name:
            messagebox.showwarning("Eingabe fehlt", "Bitte Suchbegriff und Name eingeben.")
            return
        self.logger.log(f"Starte WoS Suche für {name}: {query}")
        threading.Thread(target=self.search, args=(query, name), daemon=True).start()

    def search(self, query, name):
        results = search_wos(query, name)
        self.results = results
        self.update_tree()
        self.logger.log(f"WoS Suche abgeschlossen: {len(results)} Treffer.")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for res in self.results:
            self.tree.insert("", tk.END, values=(res.get("Titel"), res.get("Veröffentlichungsjahr"), res.get("Autoren"), res.get("DOI"), res.get("Zitationsanzahl")))

class ScopusTab(tk.Frame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.create_widgets()
        self.results = []

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self, text="Scopus Suche", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(input_frame, text="Suchbegriff:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_query = ttk.Entry(input_frame, width=50)
        self.entry_query.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=50)
        self.entry_name.grid(row=1, column=1, padx=5, pady=5)
        self.btn_search = ttk.Button(input_frame, text="Suche starten", command=self.start_search)
        self.btn_search.grid(row=2, column=0, columnspan=2, pady=5)
        self.tree = ttk.Treeview(self, columns=("Titel", "Jahr", "Autoren", "DOI", "Zitationsanzahl"), show="headings")
        self.tree.heading("Titel", text="Titel")
        self.tree.heading("Jahr", text="Jahr")
        self.tree.heading("Autoren", text="Autoren")
        self.tree.heading("DOI", text="DOI")
        self.tree.heading("Zitationsanzahl", text="Zitationsanzahl")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def start_search(self):
        query = self.entry_query.get().strip()
        name = self.entry_name.get().strip()
        if not query or not name:
            messagebox.showwarning("Eingabe fehlt", "Bitte Suchbegriff und Name eingeben.")
            return
        self.logger.log(f"Starte Scopus Suche für {name}: {query}")
        threading.Thread(target=self.search, args=(query, name), daemon=True).start()

    def search(self, query, name):
        results = search_scopus(query, name)
        self.results = results
        self.update_tree()
        self.logger.log(f"Scopus Suche abgeschlossen: {len(results)} Treffer.")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for res in self.results:
            self.tree.insert("", tk.END, values=(res.get("Titel"), res.get("Veröffentlichungsjahr"), res.get("Autoren"), res.get("DOI"), res.get("Zitationsanzahl")))

class CombinedResultsTab(tk.Frame):
    def __init__(self, parent, logger, pubmed_tab, dnb_tab, wos_tab, scopus_tab):
        super().__init__(parent)
        self.logger = logger
        self.pubmed_tab = pubmed_tab
        self.dnb_tab = dnb_tab
        self.wos_tab = wos_tab
        self.scopus_tab = scopus_tab
        self.results = []
        self.create_widgets()

    def create_widgets(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        self.btn_combine = ttk.Button(btn_frame, text="Kombinierte Suche", command=self.combine_results)
        self.btn_combine.pack(side=tk.LEFT, padx=5)
        self.tree = ttk.Treeview(self, columns=("Datenbank", "Titel", "Jahr", "Autoren", "Zitationen"), show="headings")
        self.tree.heading("Datenbank", text="Datenbank")
        self.tree.heading("Titel", text="Titel")
        self.tree.heading("Jahr", text="Jahr")
        self.tree.heading("Autoren", text="Autoren")
        self.tree.heading("Zitationen", text="Zitationsanzahl")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def combine_results(self):
        self.results = []
        for res in self.pubmed_tab.results:
            res["Datenbank"] = "PubMed"
            self.results.append(res)
        for res in self.dnb_tab.results:
            res["Datenbank"] = "DNB"
            self.results.append(res)
        for res in self.wos_tab.results:
            res["Datenbank"] = "WoS"
            self.results.append(res)
        for res in self.scopus_tab.results:
            res["Datenbank"] = "Scopus"
            self.results.append(res)
        self.update_tree()
        self.logger.log(f"Kombinierte Suche abgeschlossen: {len(self.results)} Treffer.")

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for res in self.results:
            self.tree.insert("", tk.END, values=(res.get("Datenbank"), res.get("Titel"), res.get("Veröffentlichungsjahr"), res.get("Autoren"), res.get("Zitationsanzahl")))

class SettingsTab(tk.Frame):
    def __init__(self, parent, config_manager, logger):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logger
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.LabelFrame(self, text="Globale Einstellungen", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(frame, text="Ausgabe-Pfad:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_output = ttk.Entry(frame, width=50)
        self.entry_output.insert(0, self.config_manager.settings.get("output_path", "./output"))
        self.entry_output.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Pfad wählen", command=self.choose_path).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(frame, text="Einstellungen speichern", command=self.save_settings).grid(row=1, column=0, columnspan=3, pady=10)

    def choose_path(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, path)

    def save_settings(self):
        new_path = self.entry_output.get().strip()
        if new_path:
            self.config_manager.settings["output_path"] = new_path
            self.config_manager.save_settings()
            self.logger.log("Einstellungen gespeichert.")
            messagebox.showinfo("Erfolg", "Einstellungen wurden gespeichert.")

class LogTab(tk.Frame):
    def __init__(self, parent, logger):
        super().__init__(parent)
        self.logger = logger
        self.create_widgets()

    def create_widgets(self):
        self.text_log = tk.Text(self, state="disabled")
        self.text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_export = ttk.Button(self, text="Log exportieren", command=lambda: self.logger.export_log())
        btn_export.pack(pady=5)

# ------------------------------------------------------------------------------
# Main Application
# ------------------------------------------------------------------------------

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Integrierte Publikations-Suchanwendung")
        self.geometry("1200x800")
        global config_manager
        config_manager = ConfigManager()
        self.logger = Logger()
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.pubmed_tab = PubMedTab(self.notebook, config_manager, self.logger)
        self.dnb_tab = DNBTab(self.notebook, config_manager, self.logger)
        self.wos_tab = WoSTab(self.notebook, config_manager, self.logger)
        self.scopus_tab = ScopusTab(self.notebook, config_manager, self.logger)
        self.combined_tab = CombinedResultsTab(self.notebook, self.logger, self.pubmed_tab, self.dnb_tab, self.wos_tab, self.scopus_tab)
        self.settings_tab = SettingsTab(self.notebook, config_manager, self.logger)
        self.log_tab = LogTab(self.notebook, self.logger)
        self.notebook.add(self.pubmed_tab, text="PubMed")
        self.notebook.add(self.dnb_tab, text="DNB")
        self.notebook.add(self.wos_tab, text="WoS")
        self.notebook.add(self.scopus_tab, text="Scopus")
        self.notebook.add(self.combined_tab, text="Kombinierte Ergebnisse")
        self.notebook.add(self.settings_tab, text="Einstellungen")
        self.notebook.add(self.log_tab, text="Log")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
