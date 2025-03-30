#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrierte Publikations-Suchanwendung

Diese Anwendung vereint die Suchfunktionalitäten von PubMed, DNB, Web of Science und Scopus.
Sie bietet separate Tabs für jede Datenbank sowie eine kombinierte Suche und umfassende 
Konfigurations-, Analyse- und Exportmöglichkeiten.

Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import os
import json
import time
import threading
import requests
import xml.etree.ElementTree as ET
import asyncio
import aiohttp
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
from functools import lru_cache
import sys
import csv
import re

# Konfigurationsdatei
CONFIG_FILE = "medicalspytool_config.json"

# Globale Variablen
GLOBAL_LOG = []
search_results = []

# Namespace Dictionary für DNB
DNB_NS = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/'
}

#######################################
# Logging und Hilfsfunktionen
#######################################

def setup_logging():
    """Konfiguriert das Logging für die Anwendung."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("medicalspytool.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("MedicalSpyTool")

logger = setup_logging()

def log_message(log_widget, message):
    """Fügt eine Nachricht zum Log hinzu und zeigt sie im Widget an."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    GLOBAL_LOG.append(full_msg)
    
    logger.info(message)
    
    if log_widget:
        try:
            log_widget.config(state="normal")
            log_widget.insert(tk.END, full_msg)
            log_widget.see(tk.END)
            log_widget.config(state="disabled")
        except Exception as e:
            print(f"Fehler beim Logging im GUI: {e}")
    else:
        print(full_msg.strip())

def clear_log(log_widget):
    """Löscht den Inhalt des Logs."""
    global GLOBAL_LOG
    GLOBAL_LOG = []
    log_widget.config(state="normal")
    log_widget.delete("1.0", tk.END)
    log_widget.config(state="disabled")

def export_log(log_widget):
    """Exportiert den Log in eine Datei."""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Dateien", "*.txt"), ("Alle Dateien", "*.*")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(GLOBAL_LOG))
        messagebox.showinfo("Log exportiert", f"Log wurde in {file_path} gespeichert.")

#######################################
# Konfigurationsmanagement
#######################################

def load_settings():
    """Lädt die Einstellungen aus der Konfigurationsdatei."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        logger.info("Einstellungen geladen.")
        return settings
    except FileNotFoundError:
        settings = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "pubmed_api_key": "",
            "wos_api_key": "",
            "scopus_api_key": "",
            "output_columns": [
                "Datenbank", "Name", "Titel", "Erscheinungsjahr", "Autoren", 
                "Identifier", "URL", "Zitationsanzahl"
            ],
            "default_database": "Kombiniert"
        }
        save_settings(settings)
        logger.info("Standard-Einstellungen erstellt.")
        return settings

def save_settings(settings):
    """Speichert die Einstellungen in der Konfigurationsdatei."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    logger.info("Einstellungen gespeichert.")

#######################################
# Abstrakte Datenbankconnector-Klasse
#######################################

class DatabaseConnector:
    """Basisklasse für Datenbankverbindungen."""
    
    def __init__(self, api_key=None, settings=None):
        self.api_key = api_key
        self.settings = settings or {}
        self.name = "Generic Database"
        self.max_results_per_page = 100
        self.search_fields = []
        
    def search(self, query, params=None, log_widget=None):
        """In Unterklassen zu implementieren"""
        raise NotImplementedError("Diese Methode muss in Unterklassen implementiert werden")
        
    def parse_results(self, response):
        """In Unterklassen zu implementieren"""
        raise NotImplementedError("Diese Methode muss in Unterklassen implementiert werden")
        
    def get_citation_count(self, id):
        """In Unterklassen zu implementieren"""
        return "N/A"
    
    def get_available_fields(self):
        """Gibt die verfügbaren Suchfelder zurück"""
        return self.search_fields
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """Standard-Implementierung für den Aufbau einer Abfrage"""
        query = base_query
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
        return query

#######################################
# PubMed Connector Implementierung
#######################################

class PubMedConnector(DatabaseConnector):
    """Connector für PubMed."""
    
    def __init__(self, api_key=None, settings=None):
        super().__init__(api_key, settings)
        self.name = "PubMed"
        self.max_results_per_page = 1000
        self.search_fields = ["Alle Felder", "Autor", "Titel", "Journal", "MESH-Terme"]
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    @lru_cache(maxsize=128)
    def get_citation_count(self, pmid):
        """Ruft die Zitationsanzahl für eine PubMed-ID ab."""
        if not pmid or pmid == "N/A":
            return "N/A"
            
        elink_url = self.base_url + "elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": pmid,
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        max_retries = 3
        delay = 0.5
        
        for attempt in range(max_retries):
            try:
                response = requests.get(elink_url, params=params)
                response.raise_for_status()
                xml_data = ET.fromstring(response.content)
                count = len(xml_data.findall(".//LinkSetDb/Link/Id"))
                return count
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Too Many Requests
                    logger.warning(f"429 Fehler für PMID {pmid}. Warte {delay} Sekunden...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Fehler beim Abrufen der Zitationsanzahl für PMID {pmid}: {e}")
                    return "Fehler"
            except ET.ParseError as e:
                logger.error(f"Parse-Fehler für PMID {pmid}: {e}")
                return "Fehler XML"
                
        logger.error(f"Maximale Wiederholungen für PMID {pmid} überschritten.")
        return "Fehler 429"
    
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """Baut eine PubMed-Suchanfrage auf."""
        query = base_query

        if field and field != "Alle Felder":
            field_map = {
                "Autor": "[Author]",
                "Titel": "[Title]",
                "Journal": "[Journal]",
                "MESH-Terme": "[MeSH Terms]"
            }
            query = f"{query}{field_map.get(field, '')}"

        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
            
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].strftime("%Y/%m/%d")
            end_date = date_range['end'].strftime("%Y/%m/%d")
            query = f"{query} AND {start_date}:{end_date}[Date - Publication]"
            
        if language:
            query = f"{query} AND {language}[Language]"
            
        if pub_type:
            query = f"{query} AND {pub_type}[Publication Type]"
            
        return query
    
    def search(self, query, params=None, log_widget=None):
        """Führt eine Suche in PubMed durch."""
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        max_results = params.get('max_results', 1000)
        
        log_message(log_widget, f"PubMed-Suche gestartet: {query}")
        
        esearch_url = self.base_url + "esearch.fcgi"
        efetch_url = self.base_url + "efetch.fcgi"
        
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(esearch_url, params=esearch_params)
            response.raise_for_status()
            esearch_xml = ET.fromstring(response.content)
            id_list = [node.text for node in esearch_xml.findall(".//Id")]
            
            count_node = esearch_xml.find(".//Count")
            total_count = int(count_node.text) if count_node is not None else 0
            
            log_message(log_widget, f"PubMed-Suche: {total_count} Ergebnisse gefunden")
            
            if not id_list:
                log_message(log_widget, f"Keine Publikationen für '{query}' gefunden.")
                return []
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Fehler bei der PubMed-Suche für '{query}': {e}")
            return []
        
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        try:
            log_message(log_widget, f"Rufe PubMed-Detaildaten für {len(id_list)} Artikel ab...")
            response = requests.get(efetch_url, params=efetch_params)
            response.raise_for_status()
            efetch_xml = ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Fehler beim Abrufen der PubMed-Detaildaten: {e}")
            return []
        
        return self.parse_results(efetch_xml, name, log_widget)
    
    def parse_results(self, efetch_xml, name, log_widget):
        """Analysiert die PubMed-XML-Antwort und extrahiert relevante Daten."""
        publications = []
        articles = efetch_xml.findall(".//PubmedArticle")
        total = len(articles)
        
        log_message(log_widget, f"Beginne mit der Verarbeitung von {total} PubMed-Artikeln...")
        
        for i, article in enumerate(articles):
            if i % 10 == 0:  # Status-Update alle 10 Artikel
                log_message(log_widget, f"Verarbeite PubMed-Artikel {i+1}/{total}...")
                
            try:
                title_el = article.find(".//ArticleTitle")
                title = title_el.text if title_el is not None else "Kein Titel"
                
                # Verarbeitung des Publikationsdatums
                pub_date_el = article.find(".//PubDate")
                year = pub_date_el.find("Year").text if pub_date_el is not None and pub_date_el.find("Year") is not None else "N/A"
                
                # Autoren extrahieren
                authors = []
                for author in article.findall(".//Author"):
                    ln = author.find(".//LastName")
                    fn = author.find(".//ForeName")
                    if ln is not None and fn is not None:
                        authors.append(f"{fn.text} {ln.text}")
                    elif ln is not None:
                        authors.append(ln.text)
                authors_str = ", ".join(authors) if authors else "N/A"
                
                # Publikationstypen
                pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
                pub_types_str = ", ".join(pub_types) if pub_types else "N/A"
                
                # IDs und URLs
                pmid_el = article.find(".//PMID")
                pmid = pmid_el.text if pmid_el is not None else "N/A"
                
                doi_el = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_el.text if doi_el is not None else "N/A"
                
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "N/A" else "N/A"
                doi_url = f"https://doi.org/{doi}" if doi != "N/A" else "N/A"
                
                # Zitationsanzahl abrufen
                citation_count = self.get_citation_count(pmid)
                
                # Publikation zum Ergebnis hinzufügen
                publications.append({
                    "Datenbank": "PubMed",
                    "Name": name,
                    "Titel": title,
                    "Erscheinungsjahr": year,
                    "Autoren": authors_str,
                    "Publikationstypen": pub_types_str,
                    "PubMed-ID": pmid,
                    "DOI": doi,
                    "URL": pubmed_url,
                    "DOI-URL": doi_url,
                    "Zitationsanzahl": citation_count
                })
                
            except Exception as e:
                log_message(log_widget, f"Fehler beim Parsen eines PubMed-Artikels: {e}")
                
        log_message(log_widget, f"PubMed-Ergebnisse verarbeitet: {len(publications)} Publikationen")
        return publications

#######################################
# DNB Connector Implementierung
#######################################

class DNBConnector(DatabaseConnector):
    """Connector für die Deutsche Nationalbibliothek."""
    
    def __init__(self, api_key=None, settings=None):
        super().__init__(api_key, settings)
        self.name = "Deutsche Nationalbibliothek"
        self.max_results_per_page = 100
        self.search_fields = ["Alle Felder", "Titel", "Autor", "Schlagwort", "Jahr"]
        self.base_url = "https://services.dnb.de/sru/dnb"
    
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """Baut eine CQL-Abfrage für die DNB."""
        # Transformiert den Suchbegriff für DNB-Format
        query = self.transform_query(base_query, field)
        
        # Zusätzliche Suchbegriffe
        if additional_terms:
            add_terms = self.transform_query(additional_terms, "Alle Felder")
            query = f"({query}) AND ({add_terms})"
        
        # Datumsbereich
        if date_range and date_range.get('start') and date_range.get('end'):
            start_year = date_range['start'].year
            end_year = date_range['end'].year
            query += f" AND jhr >= {start_year} AND jhr <= {end_year}"
        
        # Sprache
        if language:
            query += f" AND sprache = {language}"
        
        return query
    
    def transform_query(self, query, field="Alle Felder"):
        """Transformiert eine Suchabfrage in das CQL-Format der DNB."""
        field_map = {
            "Alle Felder": "allfields",
            "Titel": "tit",
            "Autor": "per",
            "Schlagwort": "sw",
            "Jahr": "jhr"
        }
        
        dnb_field = field_map.get(field, "allfields")
        
        # Einfache Bereinigung des Query-Strings
        query = query.replace('"', '\\"').strip()
        
        # Erweiterte Bereinigung für CQL
        if ' ' in query and not (query.startswith('"') and query.endswith('"')):
            terms = query.split()
            # Bei mehreren Wörtern: Einzelne Terme mit AND verknüpfen
            if len(terms) > 1:
                query = " AND ".join([f'{dnb_field} = "{term}"' for term in terms])
            else:
                query = f'{dnb_field} = "{query}"'
        else:
            # Bei Einzelwörtern oder bereits in Anführungszeichen
            if query.startswith('"') and query.endswith('"'):
                query = f'{dnb_field} = {query}'
            else:
                query = f'{dnb_field} = "{query}"'
                
        return query
    
    def search(self, query, params=None, log_widget=None):
        """Führt eine Suche in der DNB durch."""
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        max_results = params.get('max_results', 100)
        start_record = params.get('start_record', 1)
        
        log_message(log_widget, f"DNB-Suche gestartet: {query}")
        
        search_params = {
            "operation": "searchRetrieve",
            "version": "1.1",
            "query": query,
            "maximumRecords": max_results,
            "startRecord": start_record,
            "recordSchema": "RDFxml"
        }
        
        try:
            response = requests.get(self.base_url, params=search_params)
            response.raise_for_status()
            
            # XML-Antwort parsen
            root = ET.fromstring(response.content)
            
            # Anzahl der gefundenen Datensätze
            num_records_node = root.find(".//srw:numberOfRecords", DNB_NS)
            total_records = int(num_records_node.text) if num_records_node is not None else 0
            
            log_message(log_widget, f"DNB-Suche: {total_records} Ergebnisse gefunden")
            
            if total_records == 0:
                return []
                
            # Ergebnisse parsen
            results = self.parse_results(root, name, log_widget)
            
            return results
            
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Fehler bei der DNB-Suche: {e}")
            return []
        except ET.ParseError as e:
            log_message(log_widget, f"Fehler beim Parsen der DNB-Antwort: {e}")
            return []
    
    def parse_results(self, root, name, log_widget):
        """Extrahiert die Informationen aus der XML-Antwort der DNB."""
        results = []
        records = root.findall(".//srw:record", DNB_NS)
        total = len(records)
        
        log_message(log_widget, f"Beginne mit der Verarbeitung von {total} DNB-Datensätzen...")
        
        for i, record in enumerate(records):
            if i % 10 == 0:  # Status-Update alle 10 Datensätze
                log_message(log_widget, f"Verarbeite DNB-Datensatz {i+1}/{total}...")
                
            try:
                # Extrahiere recordData
                record_data = record.find(".//srw:recordData", DNB_NS)
                if record_data is None:
                    continue
                    
                # Titel extrahieren
                title_elements = record_data.findall(".//*[@property='http://purl.org/dc/terms/title']", DNB_NS) or \
                                record_data.findall(".//dc:title", DNB_NS)
                title = title_elements[0].text if title_elements else "N/A"
                
                # Autoren/Ersteller extrahieren
                creator_elements = record_data.findall(".//dc:creator", DNB_NS)
                creators = [creator.text for creator in creator_elements if creator.text]
                creator_str = "; ".join(creators) if creators else "N/A"
                
                # Erscheinungsjahr extrahieren
                year_elements = record_data.findall(".//dcterms:issued", DNB_NS) or \
                               record_data.findall(".//dc:date", DNB_NS)
                year = year_elements[0].text if year_elements else "N/A"
                
                # Identifikator extrahieren (ISBN, ISSN, usw.)
                identifier_elements = record_data.findall(".//dc:identifier", DNB_NS)
                identifiers = []
                for identifier in identifier_elements:
                    if identifier.text and identifier.text.strip():
                        identifiers.append(identifier.text.strip())
                identifier_str = "; ".join(identifiers) if identifiers else "N/A"
                
                # Verleger extrahieren
                publisher_elements = record_data.findall(".//dc:publisher", DNB_NS)
                publisher = publisher_elements[0].text if publisher_elements else "N/A"
                
                # Sprache extrahieren
                language_elements = record_data.findall(".//dc:language", DNB_NS)
                language = language_elements[0].text if language_elements else "N/A"
                
                # DNB-ID für URL
                dnb_id = ""
                for identifier in identifiers:
                    if identifier.startswith("http://d-nb.info/"):
                        dnb_id = identifier
                        break
                
                # Dokumenttyp extrahieren
                type_elements = record_data.findall(".//dc:type", DNB_NS)
                doc_type = type_elements[0].text if type_elements else "N/A"
                
                # Ergebnis als Dictionary hinzufügen
                results.append({
                    "Datenbank": "DNB",
                    "Name": name,
                    "Titel": title,
                    "Erscheinungsjahr": year,
                    "Autoren": creator_str,
                    "Publisher": publisher,
                    "Sprache": language,
                    "Dokumenttyp": doc_type,
                    "Identifier": identifier_str,
                    "URL": dnb_id if dnb_id else "N/A"
                })
            except Exception as e:
                log_message(log_widget, f"Fehler beim Parsen eines DNB-Datensatzes: {e}")
                
        log_message(log_widget, f"DNB-Ergebnisse verarbeitet: {len(results)} Publikationen")
        return results

#######################################
# Web of Science Connector Implementierung
#######################################

class WoSConnector(DatabaseConnector):
    """Connector für Web of Science."""
    
    def __init__(self, api_key=None, settings=None):
        super().__init__(api_key, settings)
        self.name = "Web of Science"
        self.max_results_per_page = 50
        self.search_fields = ["Alle Felder", "Autor", "Titel", "Thema", "Journal"]
        self.base_url = "https://wos-api.clarivate.com/api/v1"
        self.dummy_mode = True if not api_key else False  # Dummy-Modus, wenn kein API-Key vorhanden
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """Baut eine Web of Science-Suchanfrage auf."""
        field_map = {
            "Alle Felder": "ALL",
            "Autor": "AU",
            "Titel": "TI",
            "Thema": "TS",
            "Journal": "SO"
        }
        
        wos_field = field_map.get(field, "ALL")
        
        # Basis-Query formatieren
        query = f"{wos_field}=({base_query})"
        
        # Zusätzliche Suchbegriffe
        if additional_terms:
            query = f"{query} AND ALL=({additional_terms})"
            
        # Datumsbereich
        if date_range and date_range.get('start') and date_range.get('end'):
            start_year = date_range['start'].year
            end_year = date_range['end'].year
            query = f"{query} AND PY=({start_year}-{end_year})"
            
        # Sprache
        if language:
            query = f"{query} AND LA=({language})"
            
        # Publikationstyp
        if pub_type:
            query = f"{query} AND DT=({pub_type})"
            
        return query
    
    def search(self, query, params=None, log_widget=None):
        """Führt eine Suche in Web of Science durch."""
        if self.dummy_mode:
            log_message(log_widget, "WoS-Suche im Dummy-Modus, da kein API-Key vorhanden ist.")
            return self._dummy_search(query, params, log_widget)
            
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        max_results = min(params.get('max_results', 50), 1000)  # WoS API Limite
        
        log_message(log_widget, f"Web of Science-Suche gestartet: {query}")
        
        headers = {
            "X-ApiKey": self.api_key,
            "Content-Type": "application/json"
        }
        
        search_params = {
            "query": query,
            "count": min(max_results, 50),  # Max 50 pro Anfrage
            "offset": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=search_params
            )
            response.raise_for_status()
            data = response.json()
            
            total_records = data.get("QueryResult", {}).get("RecordsFound", 0)
            log_message(log_widget, f"WoS-Suche: {total_records} Ergebnisse gefunden")
            
            if total_records == 0:
                return []
                
            records = data.get("Data", {}).get("Records", [])
            results = []
            
            # Hole weitere Seiten, falls nötig
            offset = 51
            while len(records) < min(total_records, max_results) and offset < max_results:
                search_params["offset"] = offset
                log_message(log_widget, f"Hole weitere WoS-Ergebnisse (Offset: {offset})...")
                
                response = requests.post(
                    f"{self.base_url}/search",
                    headers=headers,
                    json=search_params
                )
                response.raise_for_status()
                data = response.json()
                
                additional_records = data.get("Data", {}).get("Records", [])
                if not additional_records:
                    break
                    
                records.extend(additional_records)
                offset += 50
                
            return self.parse_results(records, name, log_widget)
            
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Fehler bei der WoS-Suche: {e}")
            return []
    
    def _dummy_search(self, query, params=None, log_widget=None):
        """Generiert Dummy-Ergebnisse für Tests ohne API-Key."""
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        
        log_message(log_widget, f"Generiere Dummy-Ergebnisse für WoS-Suche: {query}")
        
        # Erstelle 5 Dummy-Ergebnisse
        results = []
        for i in range(1, 6):
            results.append({
                "Datenbank": "Web of Science (Dummy)",
                "Name": name,
                "Titel": f"Dummy WoS Artikel {i} für {query}",
                "Erscheinungsjahr": str(2020 - i),
                "Autoren": f"Autor A, Autor B, Autor C",
                "Journal": f"Journal of Dummy Science {i}",
                "Zitationsanzahl": str(10 * i),
                "URL": "https://www.webofscience.com/",
                "DOI": f"10.1000/dummy.{i}",
                "WoS-ID": f"WOS:00000000{i}"
            })
            
        log_message(log_widget, f"WoS-Dummy-Ergebnisse generiert: {len(results)} Publikationen")
        return results
    
    def parse_results(self, records, name, log_widget):
        """Parst die Ergebnisse aus der WoS-API."""
        results = []
        total = len(records)
        
        log_message(log_widget, f"Beginne mit der Verarbeitung von {total} WoS-Datensätzen...")
        
        for i, record in enumerate(records):
            if i % 10 == 0:  # Status-Update alle 10 Datensätze
                log_message(log_widget, f"Verarbeite WoS-Datensatz {i+1}/{total}...")
                
            try:
                # Extrahiere die Daten
                title = record.get("Title", "N/A")
                
                # Autoren
                authors = record.get("Authors", [])
                author_str = ", ".join(authors) if authors else "N/A"
                
                # Jahr
                year = record.get("PublicationYear", "N/A")
                
                # Journal/Quelle
                source = record.get("Source", "N/A")
                
                # DOI
                doi = record.get("DOI", "N/A")
                
                # Zitationsanzahl
                citations = record.get("CitationCount", "N/A")
                
                # WoS-ID
                wos_id = record.get("UID", "N/A")
                
                # URL
                url = f"https://www.webofscience.com/wos/woscc/full-record/{wos_id}" if wos_id != "N/A" else "N/A"
                
                # Ergebnis als Dictionary hinzufügen
                results.append({
                    "Datenbank": "Web of Science",
                    "Name": name,
                    "Titel": title,
                    "Erscheinungsjahr": year,
                    "Autoren": author_str,
                    "Journal": source,
                    "Zitationsanzahl": citations,
                    "URL": url,
                    "DOI": doi,
                    "WoS-ID": wos_id
                })
                
            except Exception as e:
                log_message(log_widget, f"Fehler beim Parsen eines WoS-Datensatzes: {e}")
                
        log_message(log_widget, f"WoS-Ergebnisse verarbeitet: {len(results)} Publikationen")
        return results

#######################################
# Scopus Connector Implementierung
#######################################

class ScopusConnector(DatabaseConnector):
    """Connector für Scopus."""
    
    def __init__(self, api_key=None, settings=None):
        super().__init__(api_key, settings)
        self.name = "Scopus"
        self.max_results_per_page = 25
        self.search_fields = ["Alle Felder", "Autor", "Titel", "Schlüsselwörter", "Abstract", "ISSN"]
        self.base_url = "https://api.elsevier.com/content/search/scopus"
        self.dummy_mode = True if not api_key else False  # Dummy-Modus, wenn kein API-Key vorhanden
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """Baut eine Scopus-Suchanfrage auf."""
        field_map = {
            "Alle Felder": "ALL",
            "Autor": "AUTH",
            "Titel": "TITLE",
            "Schlüsselwörter": "KEY",
            "Abstract": "ABS",
            "ISSN": "ISSN"
        }
        
        scopus_field = field_map.get(field, "ALL")
        
        # Basis-Query formatieren
        query = f"{scopus_field}({base_query})"
        
        # Zusätzliche Suchbegriffe
        if additional_terms:
            query = f"{query} AND ALL({additional_terms})"
            
        # Datumsbereich
        if date_range and date_range.get('start') and date_range.get('end'):
            start_year = date_range['start'].year
            end_year = date_range['end'].year
            query = f"{query} AND PUBYEAR AFT {start_year-1} AND PUBYEAR BEF {end_year+1}"
            
        # Sprache
        if language:
            query = f"{query} AND LANGUAGE({language})"
            
        # Publikationstyp
        if pub_type:
            query = f"{query} AND DOCTYPE({pub_type})"
            
        return query
    
    def search(self, query, params=None, log_widget=None):
        """Führt eine Suche in Scopus durch."""
        if self.dummy_mode:
            log_message(log_widget, "Scopus-Suche im Dummy-Modus, da kein API-Key vorhanden ist.")
            return self._dummy_search(query, params, log_widget)
            
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        max_results = min(params.get('max_results', 100), 200)  # Begrenzen auf 200
        
        log_message(log_widget, f"Scopus-Suche gestartet: {query}")
        
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        
        search_params = {
            "query": query,
            "count": min(max_results, 25),  # Max 25 pro Anfrage
            "start": 0,
            "view": "COMPLETE"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=search_params)
            response.raise_for_status()
            data = response.json()
            
            total_results = int(data.get("search-results", {}).get("opensearch:totalResults", "0"))
            log_message(log_widget, f"Scopus-Suche: {total_results} Ergebnisse gefunden")
            
            if total_results == 0:
                return []
                
            entries = data.get("search-results", {}).get("entry", [])
            results = []
            
            # Hole weitere Seiten, falls nötig
            start = min(max_results, 25)
            while len(entries) < min(total_results, max_results) and start < max_results:
                search_params["start"] = start
                log_message(log_widget, f"Hole weitere Scopus-Ergebnisse (Start: {start})...")
                
                response = requests.get(self.base_url, headers=headers, params=search_params)
                response.raise_for_status()
                data = response.json()
                
                additional_entries = data.get("search-results", {}).get("entry", [])
                if not additional_entries:
                    break
                    
                entries.extend(additional_entries)
                start += 25
                
            return self.parse_results(entries, name, log_widget)
            
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Fehler bei der Scopus-Suche: {e}")
            return []
    
    def _dummy_search(self, query, params=None, log_widget=None):
        """Generiert Dummy-Ergebnisse für Tests ohne API-Key."""
        params = params or {}
        name = params.get('name', 'Allgemeine Suche')
        
        log_message(log_widget, f"Generiere Dummy-Ergebnisse für Scopus-Suche: {query}")
        
        # Erstelle 5 Dummy-Ergebnisse
        results = []
        for i in range(1, 6):
            results.append({
                "Datenbank": "Scopus (Dummy)",
                "Name": name,
                "Titel": f"Dummy Scopus Artikel {i} für {query}",
                "Erscheinungsjahr": str(2020 - i),
                "Autoren": f"Autor X, Autor Y, Autor Z",
                "Journal": f"Scopus Journal of Science {i}",
                "Zitationsanzahl": str(5 * i),
                "URL": "https://www.scopus.com/",
                "DOI": f"10.2000/dummy.{i}",
                "Scopus-ID": f"SCOPUS:000000000{i}"
            })
            
        log_message(log_widget, f"Scopus-Dummy-Ergebnisse generiert: {len(results)} Publikationen")
        return results
    
    def parse_results(self, entries, name, log_widget):
        """Parst die Ergebnisse aus der Scopus-API."""
        results = []
        total = len(entries)
        
        log_message(log_widget, f"Beginne mit der Verarbeitung von {total} Scopus-Datensätzen...")
        
        for i, entry in enumerate(entries):
            if i % 10 == 0:  # Status-Update alle 10 Datensätze
                log_message(log_widget, f"Verarbeite Scopus-Datensatz {i+1}/{total}...")
                
            try:
                # Extrahiere die Daten
                title = entry.get("dc:title", "N/A")
                
                # Autoren
                authors = entry.get("dc:creator", "N/A")
                
                # Jahr
                year = entry.get("prism:coverDate", "N/A")
                if year and year != "N/A":
                    try:
                        year = year.split("-")[0]  # Format YYYY-MM-DD zu YYYY
                    except:
                        pass
                
                # Journal/Quelle
                source = entry.get("prism:publicationName", "N/A")
                
                # DOI
                doi = entry.get("prism:doi", "N/A")
                
                # Zitationsanzahl
                citations = entry.get("citedby-count", "N/A")
                
                # Scopus-ID
                scopus_id = entry.get("dc:identifier", "N/A")
                if scopus_id.startswith("SCOPUS_ID:"):
                    scopus_id = scopus_id.replace("SCOPUS_ID:", "")
                
                # URL
                url = entry.get("prism:url", "N/A")
                
                # Ergebnis als Dictionary hinzufügen
                results.append({
                    "Datenbank": "Scopus",
                    "Name": name,
                    "Titel": title,
                    "Erscheinungsjahr": year,
                    "Autoren": authors,
                    "Journal": source,
                    "Zitationsanzahl": citations,
                    "URL": url,
                    "DOI": doi,
                    "Scopus-ID": scopus_id
                })
                
            except Exception as e:
                log_message(log_widget, f"Fehler beim Parsen eines Scopus-Datensatzes: {e}")
                
        log_message(log_widget, f"Scopus-Ergebnisse verarbeitet: {len(results)} Publikationen")
        return results

#######################################
# Export- und Analysefunktionen
#######################################

def export_to_excel(results, file_path, log_widget=None):
    """Exportiert Ergebnisse in eine Excel-Datei."""
    if not results:
        log_message(log_widget, "Keine Ergebnisse zum Exportieren vorhanden.")
        return False
        
    try:
        df = pd.DataFrame(results)
        df.to_excel(file_path, index=False)
        log_message(log_widget, f"Ergebnisse erfolgreich nach {file_path} exportiert.")
        return True
    except Exception as e:
        log_message(log_widget, f"Fehler beim Export nach Excel: {e}")
        return False

def export_to_csv(results, file_path, log_widget=None):
    """Exportiert Ergebnisse in eine CSV-Datei."""
    if not results:
        log_message(log_widget, "Keine Ergebnisse zum Exportieren vorhanden.")
        return False
        
    try:
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        log_message(log_widget, f"Ergebnisse erfolgreich nach {file_path} exportiert.")
        return True
    except Exception as e:
        log_message(log_widget, f"Fehler beim Export nach CSV: {e}")
        return False

def create_year_distribution_plot(results, figure):
    """Erstellt ein Balkendiagramm zur Verteilung nach Jahren."""
    try:
        # DataFrame erstellen
        df = pd.DataFrame(results)
        
        # Sicherstellen, dass Erscheinungsjahr vorhanden ist
        if "Erscheinungsjahr" not in df.columns:
            return False
        
        # Nur numerische Jahre für das Diagramm verwenden
        df['Jahr'] = pd.to_numeric(df['Erscheinungsjahr'], errors='coerce')
        df = df.dropna(subset=['Jahr'])
        
        # Jahr in Integer umwandeln
        df['Jahr'] = df['Jahr'].astype(int)
        
        # Anzahl der Publikationen pro Jahr zählen
        year_counts = df['Jahr'].value_counts().sort_index()
        
        # Leere vorherige Figur
        figure.clear()
        ax = figure.add_subplot(111)
        
        # Balkendiagramm erstellen
        year_counts.plot(kind='bar', ax=ax)
        ax.set_title('Veröffentlichungen nach Jahr')
        ax.set_xlabel('Jahr')
        ax.set_ylabel('Anzahl')
        
        figure.tight_layout()
        return True
    except Exception as e:
        print(f"Fehler bei der Erstellung des Jahresverteilungsdiagramms: {e}")
        return False

def create_database_distribution_plot(results, figure):
    """Erstellt ein Kuchendiagramm zur Verteilung nach Datenbanken."""
    try:
        # DataFrame erstellen
        df = pd.DataFrame(results)
        
        # Sicherstellen, dass Datenbank vorhanden ist
        if "Datenbank" not in df.columns:
            return False
            
        # Anzahl der Publikationen pro Datenbank zählen
        db_counts = df['Datenbank'].value_counts()
        
        # Leere vorherige Figur
        figure.clear()
        ax = figure.add_subplot(111)
        
        # Kuchendiagramm erstellen
        ax.pie(db_counts, labels=db_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title('Verteilung nach Datenbanken')
        
        figure.tight_layout()
        return True
    except Exception as e:
        print(f"Fehler bei der Erstellung des Datenbankverteilungsdiagramms: {e}")
        return False

#######################################
# Tab-Klassen für die Benutzeroberfläche
#######################################

class BaseTab(ttk.Frame):
    """Basisklasse für alle Tabs mit gemeinsamen Funktionen."""
    
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.log_widget = None
        self.results = []
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die grundlegende UI-Struktur. In Unterklassen zu überschreiben."""
        pass
        
    def create_log_widget(self, parent):
        """Erstellt ein Log-Widget."""
        frame = ttk.LabelFrame(parent, text="Log")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar für das Log
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log-Textfeld
        log = tk.Text(frame, height=5, yscrollcommand=scrollbar.set)
        log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log.config(state="disabled")
        
        scrollbar.config(command=log.yview)
        
        # Buttons für Log-Aktionen
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Log löschen", 
                  command=lambda: clear_log(log)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Log exportieren", 
                  command=lambda: export_log(log)).pack(side=tk.LEFT, padx=5)
                  
        return log

class CombinedSearchTab(BaseTab):
    """Tab für die kombinierte Suche in allen Datenbanken."""
    
    def __init__(self, parent, settings):
        self.active_connectors = []
        super().__init__(parent, settings)
        
    def setup_ui(self):
        """Erstellt die UI für die kombinierte Suche."""
        # Hauptframe mit zwei Spalten
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Spalte: Suchoptionen
        left_frame = ttk.LabelFrame(main_frame, text="Suchoptionen")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Rechte Spalte: Ergebnisse und Log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Suchoptionen
        search_form = ttk.Frame(left_frame)
        search_form.pack(fill=tk.X, padx=5, pady=5)
        
        # Suchbegriff
        ttk.Label(search_form, text="Suchbegriff:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.query_entry = ttk.Entry(search_form, width=30)
        self.query_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Suchfeld
        ttk.Label(search_form, text="Suchfeld:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.field_var = tk.StringVar(value="Alle Felder")
        self.field_combo = ttk.Combobox(search_form, textvariable=self.field_var, 
                                         values=["Alle Felder", "Autor", "Titel"], width=28)
        self.field_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zusätzliche Suchbegriffe
        ttk.Label(search_form, text="Zusätzliche Begriffe:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.additional_query_entry = ttk.Entry(search_form, width=30)
        self.additional_query_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zeitraum
        date_frame = ttk.LabelFrame(left_frame, text="Zeitraum")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Von:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, year=2000)
        self.start_date.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(date_frame, text="Bis:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2)
        self.end_date.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Datenbank-Auswahl
        db_frame = ttk.LabelFrame(left_frame, text="Datenbanken")
        db_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_pubmed = tk.BooleanVar(value=True)
        ttk.Checkbutton(db_frame, text="PubMed", variable=self.use_pubmed).grid(
            row=0, column=0, sticky=tk.W, pady=2)
            
        self.use_dnb = tk.BooleanVar(value=True)
        ttk.Checkbutton(db_frame, text="DNB", variable=self.use_dnb).grid(
            row=1, column=0, sticky=tk.W, pady=2)
            
        self.use_wos = tk.BooleanVar(value=False)
        ttk.Checkbutton(db_frame, text="Web of Science", variable=self.use_wos).grid(
            row=0, column=1, sticky=tk.W, pady=2)
            
        self.use_scopus = tk.BooleanVar(value=False)
        ttk.Checkbutton(db_frame, text="Scopus", variable=self.use_scopus).grid(
            row=1, column=1, sticky=tk.W, pady=2)
        
        # Weitere Optionen
        options_frame = ttk.LabelFrame(left_frame, text="Weitere Optionen")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.max_results_var = tk.StringVar(value="100")
        ttk.Label(options_frame, text="Max. Ergebnisse pro DB:").grid(
            row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(options_frame, textvariable=self.max_results_var, width=5).grid(
            row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        self.language_var = tk.StringVar(value="")
        ttk.Label(options_frame, text="Sprache:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(options_frame, textvariable=self.language_var, 
                     values=["", "ger", "eng", "fre"], width=10).grid(
            row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons für die Suche
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Suchen", command=self.start_search).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset_form).pack(
            side=tk.LEFT, padx=5)
        
        # Ergebnisbereich
        result_frame = ttk.LabelFrame(right_frame, text="Suchergebnisse")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ergebnistabelle
        columns = ("Datenbank", "Titel", "Erscheinungsjahr", "Autoren", "URL")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="extended")
        
        # Spaltenüberschriften und -breiten
        self.result_tree.heading("Datenbank", text="Datenbank")
        self.result_tree.heading("Titel", text="Titel")
        self.result_tree.heading("Erscheinungsjahr", text="Jahr")
        self.result_tree.heading("Autoren", text="Autoren")
        self.result_tree.heading("URL", text="URL")
        
        self.result_tree.column("Datenbank", width=100)
        self.result_tree.column("Titel", width=300)
        self.result_tree.column("Erscheinungsjahr", width=60, anchor=tk.CENTER)
        self.result_tree.column("Autoren", width=200)
        self.result_tree.column("URL", width=150)
        
        # Scrollbars für Ergebnistabelle
        tree_scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        tree_scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Anordnung mit Grid für korrekte Scrollbar-Positionierung
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        tree_scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_scroll_x.grid(row=1, column=0, sticky=tk.EW)
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # Rechtsklick-Menü für Ergebnistabelle
        self.context_menu = tk.Menu(self.result_tree, tearoff=0)
        self.context_menu.add_command(label="Details anzeigen", command=self.show_details)
        self.context_menu.add_command(label="URL öffnen", command=self.open_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kopieren", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exportieren (Excel)", command=lambda: self.export_results("excel"))
        self.context_menu.add_command(label="Exportieren (CSV)", command=lambda: self.export_results("csv"))
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        self.result_tree.bind("<Double-1>", lambda e: self.show_details())
        
        # Statusleiste unter der Ergebnistabelle
        status_frame = ttk.Frame(right_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=0)
        
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.result_count_var = tk.StringVar(value="0 Ergebnisse")
        result_count_label = ttk.Label(status_frame, textvariable=self.result_count_var)
        result_count_label.pack(side=tk.RIGHT)
        
        # Export-Buttons
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Nach Excel exportieren", 
                  command=lambda: self.export_results("excel")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Nach CSV exportieren", 
                  command=lambda: self.export_results("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Visualisieren", 
                  command=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Log-Bereich
        log_frame = ttk.Frame(right_frame)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.log_widget = self.create_log_widget(log_frame)
    
    def start_search(self):
        """Startet die Suche in allen ausgewählten Datenbanken."""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Eingabefehler", "Bitte geben Sie einen Suchbegriff ein.")
            return
        
        # Suchanfrage zusammenstellen
        field = self.field_var.get()
        additional_terms = self.additional_query_entry.get().strip()
        date_range = {
            'start': self.start_date.get_date(),
            'end': self.end_date.get_date()
        }
        language = self.language_var.get()
        max_results = int(self.max_results_var.get())
        
        # Zurücksetzen der Ergebnisse und UI
        self.results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_var.set("Suche läuft...")
        log_message(self.log_widget, f"Kombinierte Suche gestartet: {query}")
        
        # Datenbank-Connector vorbereiten
        self.active_connectors = []
        
        if self.use_pubmed.get():
            pubmed_api_key = self.settings.get('pubmed_api_key', '')
            self.active_connectors.append(PubMedConnector(pubmed_api_key, self.settings))
            
        if self.use_dnb.get():
            self.active_connectors.append(DNBConnector(None, self.settings))
            
        if self.use_wos.get():
            wos_api_key = self.settings.get('wos_api_key', '')
            self.active_connectors.append(WoSConnector(wos_api_key, self.settings))
            
        if self.use_scopus.get():
            scopus_api_key = self.settings.get('scopus_api_key', '')
            self.active_connectors.append(ScopusConnector(scopus_api_key, self.settings))
        
        if not self.active_connectors:
            messagebox.showwarning("Eingabefehler", "Bitte wählen Sie mindestens eine Datenbank aus.")
            self.status_var.set("Bereit")
            return
        
        # Thread für die parallele Suche starten
        threading.Thread(target=self.perform_search, args=(
            query, field, additional_terms, date_range, language, max_results), 
            daemon=True).start()
    
    def perform_search(self, query, field, additional_terms, date_range, language, max_results):
        """Führt die Suche in allen ausgewählten Datenbanken durch."""
        all_results = []
        search_threads = []
        
        # Für jede Datenbank einen Thread starten
        for connector in self.active_connectors:
            # Angepasste Abfrage für jeden Connector erstellen
            db_query = connector.construct_query(
                query, additional_terms, date_range, language, None, field)
            
            # Thread für die Suche mit diesem Connector erstellen
            search_params = {
                'name': f"Suche: {query}",
                'max_results': max_results
            }
            
            thread = threading.Thread(
                target=self.search_with_connector,
                args=(connector, db_query, search_params, all_results),
                daemon=True
            )
            search_threads.append(thread)
            thread.start()
            
        # Auf alle Threads warten
        for thread in search_threads:
            thread.join()
        
        # Ergebnisse anzeigen
        self.update_results_display(all_results)
    
    def search_with_connector(self, connector, query, search_params, results_list):
        """Führt die Suche mit einem Connector durch und fügt die Ergebnisse zur Gesamtliste hinzu."""
        try:
            log_message(self.log_widget, f"Starte Suche in {connector.name}...")
            db_results = connector.search(query, search_params, self.log_widget)
            
            if db_results:
                with threading.Lock():
                    results_list.extend(db_results)
                log_message(self.log_widget, f"{len(db_results)} Ergebnisse aus {connector.name} hinzugefügt.")
            else:
                log_message(self.log_widget, f"Keine Ergebnisse aus {connector.name} gefunden.")
                
        except Exception as e:
            log_message(self.log_widget, f"Fehler bei der Suche in {connector.name}: {e}")
    
    def update_results_display(self, results):
        """Aktualisiert die Ergebnisanzeige mit den gefundenen Publikationen."""
        self.results = results
        
        # UI-Updates müssen im Hauptthread durchgeführt werden
        self.after(0, lambda: self._update_ui_with_results())
    
    def _update_ui_with_results(self):
        """Aktualisiert die UI mit den Suchergebnissen (im Hauptthread)."""
        # Tabelle leeren
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # Ergebnisse einfügen
        for i, result in enumerate(self.results):
            self.result_tree.insert("", tk.END, values=(
                result.get("Datenbank", "N/A"),
                result.get("Titel", "N/A"),
                result.get("Erscheinungsjahr", "N/A"),
                result.get("Autoren", "N/A"),
                result.get("URL", "N/A")
            ))
            
        # Status aktualisieren
        self.status_var.set("Suche abgeschlossen")
        self.result_count_var.set(f"{len(self.results)} Ergebnisse")
        
        log_message(self.log_widget, f"Suche abgeschlossen. Insgesamt {len(self.results)} Ergebnisse gefunden.")
        
        # Globale Ergebnisliste aktualisieren
        global search_results
        search_results = self.results
    
    def reset_form(self):
        """Setzt das Formular zurück."""
        self.query_entry.delete(0, tk.END)
        self.additional_query_entry.delete(0, tk.END)
        self.field_var.set("Alle Felder")
        self.start_date.set_date(datetime(2000, 1, 1).date())
        self.end_date.set_date(datetime.now().date())
        self.language_var.set("")
        self.max_results_var.set("100")
    
    def show_context_menu(self, event):
        """Zeigt das Kontextmenü für die Ergebnistabelle an."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_details(self):
        """Zeigt Details für den ausgewählten Eintrag an."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        
        # Details-Dialog anzeigen
        details_window = tk.Toplevel(self)
        details_window.title("Publikationsdetails")
        details_window.geometry("600x400")
        details_window.minsize(600, 400)
        
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbare Textansicht für die Details
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scroll.config(command=text.yview)
        
        # Details einfügen
        text.insert(tk.END, f"Datenbank: {result.get('Datenbank', 'N/A')}\n\n")
        text.insert(tk.END, f"Titel: {result.get('Titel', 'N/A')}\n\n")
        text.insert(tk.END, f"Autoren: {result.get('Autoren', 'N/A')}\n\n")
        text.insert(tk.END, f"Erscheinungsjahr: {result.get('Erscheinungsjahr', 'N/A')}\n\n")
        
        # Spezifische Felder je nach Datenbank
        if result.get('Datenbank').startswith('PubMed'):
            text.insert(tk.END, f"Journal: {result.get('Journal', 'N/A')}\n\n")
            text.insert(tk.END, f"PubMed-ID: {result.get('PubMed-ID', 'N/A')}\n\n")
            text.insert(tk.END, f"DOI: {result.get('DOI', 'N/A')}\n\n")
            text.insert(tk.END, f"Zitationsanzahl: {result.get('Zitationsanzahl', 'N/A')}\n\n")
            text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
            if 'DOI-URL' in result:
                text.insert(tk.END, f"DOI-URL: {result.get('DOI-URL', 'N/A')}\n\n")
                
        elif result.get('Datenbank').startswith('DNB'):
            text.insert(tk.END, f"Publisher: {result.get('Publisher', 'N/A')}\n\n")
            text.insert(tk.END, f"Sprache: {result.get('Sprache', 'N/A')}\n\n")
            text.insert(tk.END, f"Dokumenttyp: {result.get('Dokumenttyp', 'N/A')}\n\n")
            text.insert(tk.END, f"Identifier: {result.get('Identifier', 'N/A')}\n\n")
            text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
            
        elif result.get('Datenbank').startswith('Web of Science'):
            text.insert(tk.END, f"Journal: {result.get('Journal', 'N/A')}\n\n")
            text.insert(tk.END, f"DOI: {result.get('DOI', 'N/A')}\n\n")
            text.insert(tk.END, f"WoS-ID: {result.get('WoS-ID', 'N/A')}\n\n")
            text.insert(tk.END, f"Zitationsanzahl: {result.get('Zitationsanzahl', 'N/A')}\n\n")
            text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
            
        elif result.get('Datenbank').startswith('Scopus'):
            text.insert(tk.END, f"Journal: {result.get('Journal', 'N/A')}\n\n")
            text.insert(tk.END, f"DOI: {result.get('DOI', 'N/A')}\n\n")
            text.insert(tk.END, f"Scopus-ID: {result.get('Scopus-ID', 'N/A')}\n\n")
            text.insert(tk.END, f"Zitationsanzahl: {result.get('Zitationsanzahl', 'N/A')}\n\n")
            text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
        
        # Text als schreibgeschützt markieren
        text.config(state=tk.DISABLED)
        
        # Button zum Schließen und URL öffnen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Schließen", 
                  command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
                  
        if result.get('URL') and result.get('URL') != 'N/A':
            ttk.Button(button_frame, text="URL öffnen", 
                      command=lambda: self.open_url_from_record(result)).pack(side=tk.RIGHT, padx=5)
    
    def open_url(self):
        """Öffnet die URL für den ausgewählten Eintrag."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        self.open_url_from_record(result)
    
    def open_url_from_record(self, record):
        """Öffnet die URL aus einem Ergebnisdatensatz."""
        url = record.get('URL')
        if url and url != 'N/A':
            import webbrowser
            try:
                webbrowser.open(url)
                log_message(self.log_widget, f"URL geöffnet: {url}")
            except Exception as e:
                log_message(self.log_widget, f"Fehler beim Öffnen der URL: {e}")
    
    def copy_selected(self):
        """Kopiert ausgewählte Einträge in die Zwischenablage."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        text = ""
        for item_id in selection:
            item_index = self.result_tree.index(item_id)
            if 0 <= item_index < len(self.results):
                result = self.results[item_index]
                text += f"{result.get('Titel', 'N/A')} ({result.get('Erscheinungsjahr', 'N/A')})\n"
                text += f"Autoren: {result.get('Autoren', 'N/A')}\n"
                text += f"URL: {result.get('URL', 'N/A')}\n\n"
        
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            log_message(self.log_widget, "Ausgewählte Einträge in Zwischenablage kopiert.")
    
    def export_results(self, format_type):
        """Exportiert die Ergebnisse in eine Datei."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse zum Exportieren vorhanden.")
            return
        
        # Standarddateiname erstellen
        default_filename = f"Suchergebnisse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_excel(self.results, file_path, self.log_widget)
                
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_csv(self.results, file_path, self.log_widget)
    
    def show_visualization(self):
        """Zeigt Visualisierungen der Ergebnisdaten an."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse für Visualisierung vorhanden.")
            return
        
        # Neues Fenster für Visualisierungen erstellen
        viz_window = tk.Toplevel(self)
        viz_window.title("Ergebnisanalyse")
        viz_window.geometry("800x600")
        viz_window.minsize(600, 400)
        
        notebook = ttk.Notebook(viz_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Jahr-Verteilung
        year_frame = ttk.Frame(notebook)
        notebook.add(year_frame, text="Verteilung nach Jahren")
        
        year_fig = plt.Figure(figsize=(8, 6), dpi=100)
        create_year_distribution_plot(self.results, year_fig)
        
        year_canvas = FigureCanvasTkAgg(year_fig, year_frame)
        year_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Datenbank-Verteilung
        db_frame = ttk.Frame(notebook)
        notebook.add(db_frame, text="Verteilung nach Datenbanken")
        
        db_fig = plt.Figure(figsize=(8, 6), dpi=100)
        create_database_distribution_plot(self.results, db_fig)
        
        db_canvas = FigureCanvasTkAgg(db_fig, db_frame)
        db_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

class PubMedTab(BaseTab):
    """Tab für die PubMed-Suche."""
    
    def __init__(self, parent, settings):
        self.connector = PubMedConnector(settings.get('pubmed_api_key', ''), settings)
        super().__init__(parent, settings)
    
    def setup_ui(self):
        """Erstellt die UI für den PubMed-Tab."""
        # Hauptframe mit zwei Spalten
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Spalte: Suchoptionen
        left_frame = ttk.LabelFrame(main_frame, text="PubMed Suchoptionen")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Rechte Spalte: Ergebnisse und Log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Suchoptionen
        search_form = ttk.Frame(left_frame)
        search_form.pack(fill=tk.X, padx=5, pady=5)
        
        # Suchbegriff
        ttk.Label(search_form, text="Suchbegriff:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.query_entry = ttk.Entry(search_form, width=30)
        self.query_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Suchfeld
        ttk.Label(search_form, text="Suchfeld:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.field_var = tk.StringVar(value="Alle Felder")
        self.field_combo = ttk.Combobox(search_form, textvariable=self.field_var, 
                                       values=self.connector.search_fields, width=28)
        self.field_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zusätzliche Suchbegriffe
        ttk.Label(search_form, text="Zusätzliche Begriffe:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.additional_query_entry = ttk.Entry(search_form, width=30)
        self.additional_query_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zeitraum
        date_frame = ttk.LabelFrame(left_frame, text="Zeitraum")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Von:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, year=2000)
        self.start_date.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(date_frame, text="Bis:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # PubMed spezifische Optionen
        pubmed_frame = ttk.LabelFrame(left_frame, text="PubMed-Optionen")
        pubmed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pubmed_frame, text="Publikationstyp:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.pub_type_var = tk.StringVar(value="")
        self.pub_type_combo = ttk.Combobox(pubmed_frame, textvariable=self.pub_type_var, 
                                          values=["", "Journal Article", "Review", "Clinical Trial", 
                                                 "Meta-Analysis", "Randomized Controlled Trial"], width=28)
        self.pub_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(pubmed_frame, text="Sprache:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.language_var = tk.StringVar(value="")
        self.language_combo = ttk.Combobox(pubmed_frame, textvariable=self.language_var, 
                                          values=["", "English", "German", "French"], width=28)
        self.language_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(pubmed_frame, text="Max. Ergebnisse:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_results_var = tk.StringVar(value="100")
        ttk.Entry(pubmed_frame, textvariable=self.max_results_var, width=5).grid(
            row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons für die Suche
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Suchen", command=self.start_search).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset_form).pack(
            side=tk.LEFT, padx=5)
        
        # API-Key-Status
        api_frame = ttk.Frame(left_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.api_status_var = tk.StringVar(value="API-Key: " + 
                                          ("Vorhanden" if self.settings.get('pubmed_api_key') 
                                           else "Nicht konfiguriert"))
        ttk.Label(api_frame, textvariable=self.api_status_var).pack(side=tk.LEFT)
        ttk.Button(api_frame, text="Konfigurieren", 
                  command=self.configure_api_key).pack(side=tk.RIGHT, padx=5)
        
        # Ergebnisbereich
        result_frame = ttk.LabelFrame(right_frame, text="PubMed-Suchergebnisse")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ergebnistabelle
        columns = ("Titel", "Erscheinungsjahr", "Autoren", "Journal", "PMID", "Zitationen")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="extended")
        
        # Spaltenüberschriften und -breiten
        self.result_tree.heading("Titel", text="Titel")
        self.result_tree.heading("Erscheinungsjahr", text="Jahr")
        self.result_tree.heading("Autoren", text="Autoren")
        self.result_tree.heading("Journal", text="Journal")
        self.result_tree.heading("PMID", text="PMID")
        self.result_tree.heading("Zitationen", text="Zitationen")
        
        self.result_tree.column("Titel", width=300)
        self.result_tree.column("Erscheinungsjahr", width=60, anchor=tk.CENTER)
        self.result_tree.column("Autoren", width=200)
        self.result_tree.column("Journal", width=150)
        self.result_tree.column("PMID", width=100, anchor=tk.CENTER)
        self.result_tree.column("Zitationen", width=80, anchor=tk.CENTER)
        
        # Scrollbars für Ergebnistabelle
        tree_scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        tree_scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Anordnung mit Grid für korrekte Scrollbar-Positionierung
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        tree_scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_scroll_x.grid(row=1, column=0, sticky=tk.EW)
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # Rechtsklick-Menü für Ergebnistabelle
        self.context_menu = tk.Menu(self.result_tree, tearoff=0)
        self.context_menu.add_command(label="Details anzeigen", command=self.show_details)
        self.context_menu.add_command(label="In PubMed öffnen", command=self.open_pubmed)
        self.context_menu.add_command(label="DOI öffnen", command=self.open_doi)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kopieren", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exportieren (Excel)", command=lambda: self.export_results("excel"))
        self.context_menu.add_command(label="Exportieren (CSV)", command=lambda: self.export_results("csv"))
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        self.result_tree.bind("<Double-1>", lambda e: self.show_details())
        
        # Statusleiste unter der Ergebnistabelle
        status_frame = ttk.Frame(right_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=0)
        
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.result_count_var = tk.StringVar(value="0 Ergebnisse")
        result_count_label = ttk.Label(status_frame, textvariable=self.result_count_var)
        result_count_label.pack(side=tk.RIGHT)
        
        # Export-Buttons
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Nach Excel exportieren", 
                  command=lambda: self.export_results("excel")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Nach CSV exportieren", 
                  command=lambda: self.export_results("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Visualisieren", 
                  command=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Log-Bereich
        log_frame = ttk.Frame(right_frame)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.log_widget = self.create_log_widget(log_frame)
        
        # Ergebnisliste
        self.results = []
    
    def configure_api_key(self):
        """Konfiguriert den PubMed API-Key."""
        current_key = self.settings.get('pubmed_api_key', '')
        api_key = simpledialog.askstring("API-Key konfigurieren", 
                                         "Geben Sie Ihren PubMed API-Key ein:",
                                         initialvalue=current_key)
        
        if api_key is not None:  # Nicht abgebrochen
            self.settings['pubmed_api_key'] = api_key
            save_settings(self.settings)
            
            # Connector aktualisieren
            self.connector = PubMedConnector(api_key, self.settings)
            
            # Status aktualisieren
            self.api_status_var.set("API-Key: " + ("Vorhanden" if api_key else "Nicht konfiguriert"))
            
            log_message(self.log_widget, "PubMed API-Key wurde aktualisiert.")
    
    def start_search(self):
        """Startet die Suche in PubMed."""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Eingabefehler", "Bitte geben Sie einen Suchbegriff ein.")
            return
        
        # Suchanfrage zusammenstellen
        field = self.field_var.get()
        additional_terms = self.additional_query_entry.get().strip()
        date_range = {
            'start': self.start_date.get_date(),
            'end': self.end_date.get_date()
        }
        language = self.language_var.get()
        pub_type = self.pub_type_var.get()
        max_results = int(self.max_results_var.get())
        
        # Zurücksetzen der Ergebnisse und UI
        self.results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_var.set("Suche läuft...")
        log_message(self.log_widget, f"PubMed-Suche gestartet: {query}")
        
        # PubMed-Query erstellen
        pubmed_query = self.connector.construct_query(
            query, additional_terms, date_range, language, pub_type, field)
        
        # Thread für die Suche starten
        threading.Thread(target=self.perform_search, 
                        args=(pubmed_query, max_results), 
                        daemon=True).start()
    
    def perform_search(self, query, max_results):
        """Führt die Suche in PubMed durch."""
        try:
            # Suchparameter
            search_params = {
                'name': f"Suche: {self.query_entry.get().strip()}",
                'max_results': max_results
            }
            
            # Suche durchführen
            results = self.connector.search(query, search_params, self.log_widget)
            
            # Ergebnisse anzeigen
            self.after(0, lambda: self.update_results_display(results))
            
        except Exception as e:
            log_message(self.log_widget, f"Fehler bei der PubMed-Suche: {e}")
            self.after(0, lambda: self.status_var.set("Fehler bei der Suche"))
    
    def update_results_display(self, results):
        """Aktualisiert die Ergebnisanzeige mit den gefundenen Publikationen."""
        self.results = results
        
        # Tabelle leeren
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # Ergebnisse einfügen
        for i, result in enumerate(self.results):
            self.result_tree.insert("", tk.END, values=(
                result.get("Titel", "N/A"),
                result.get("Erscheinungsjahr", "N/A"),
                result.get("Autoren", "N/A"),
                result.get("Journal", "N/A"),
                result.get("PubMed-ID", "N/A"),
                result.get("Zitationsanzahl", "N/A")
            ))
            
        # Status aktualisieren
        self.status_var.set("Suche abgeschlossen")
        self.result_count_var.set(f"{len(self.results)} Ergebnisse")
        
        log_message(self.log_widget, f"PubMed-Suche abgeschlossen. {len(self.results)} Ergebnisse gefunden.")
        
        # Globale Ergebnisliste aktualisieren
        global search_results
        search_results = self.results
    
    def reset_form(self):
        """Setzt das Formular zurück."""
        self.query_entry.delete(0, tk.END)
        self.additional_query_entry.delete(0, tk.END)
        self.field_var.set("Alle Felder")
        self.start_date.set_date(datetime(2000, 1, 1).date())
        self.end_date.set_date(datetime.now().date())
        self.pub_type_var.set("")
        self.language_var.set("")
        self.max_results_var.set("100")
    
    def show_context_menu(self, event):
        """Zeigt das Kontextmenü für die Ergebnistabelle an."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_details(self):
        """Zeigt Details für den ausgewählten Eintrag an."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        
        # Details-Dialog anzeigen
        details_window = tk.Toplevel(self)
        details_window.title("PubMed-Publikationsdetails")
        details_window.geometry("600x400")
        details_window.minsize(600, 400)
        
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbare Textansicht für die Details
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scroll.config(command=text.yview)
        
        # Details einfügen
        text.insert(tk.END, f"Titel: {result.get('Titel', 'N/A')}\n\n")
        text.insert(tk.END, f"Autoren: {result.get('Autoren', 'N/A')}\n\n")
        text.insert(tk.END, f"Erscheinungsjahr: {result.get('Erscheinungsjahr', 'N/A')}\n\n")
        text.insert(tk.END, f"Journal: {result.get('Journal', 'N/A')}\n\n")
        text.insert(tk.END, f"Publikationstypen: {result.get('Publikationstypen', 'N/A')}\n\n")
        text.insert(tk.END, f"PubMed-ID: {result.get('PubMed-ID', 'N/A')}\n\n")
        text.insert(tk.END, f"DOI: {result.get('DOI', 'N/A')}\n\n")
        text.insert(tk.END, f"Zitationsanzahl: {result.get('Zitationsanzahl', 'N/A')}\n\n")
        text.insert(tk.END, f"PubMed-URL: {result.get('URL', 'N/A')}\n\n")
        
        if 'DOI-URL' in result and result['DOI-URL'] != 'N/A':
            text.insert(tk.END, f"DOI-URL: {result.get('DOI-URL', 'N/A')}\n\n")
        
        # Text als schreibgeschützt markieren
        text.config(state=tk.DISABLED)
        
        # Button zum Schließen und URL öffnen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Schließen", 
                  command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
                  
        if result.get('URL') and result.get('URL') != 'N/A':
            ttk.Button(button_frame, text="In PubMed öffnen", 
                      command=lambda: self.open_url(result.get('URL'))).pack(side=tk.RIGHT, padx=5)
                      
        if result.get('DOI-URL') and result.get('DOI-URL') != 'N/A':
            ttk.Button(button_frame, text="DOI öffnen", 
                      command=lambda: self.open_url(result.get('DOI-URL'))).pack(side=tk.RIGHT, padx=5)
    
    def open_pubmed(self):
        """Öffnet die PubMed-URL für den ausgewählten Eintrag."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        if result.get('URL') and result.get('URL') != 'N/A':
            self.open_url(result.get('URL'))
    
    def open_doi(self):
        """Öffnet die DOI-URL für den ausgewählten Eintrag."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        if result.get('DOI-URL') and result.get('DOI-URL') != 'N/A':
            self.open_url(result.get('DOI-URL'))
    
    def open_url(self, url):
        """Öffnet eine URL im Standardbrowser."""
        import webbrowser
        try:
            webbrowser.open(url)
            log_message(self.log_widget, f"URL geöffnet: {url}")
        except Exception as e:
            log_message(self.log_widget, f"Fehler beim Öffnen der URL: {e}")
    
    def copy_selected(self):
        """Kopiert ausgewählte Einträge in die Zwischenablage."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        text = ""
        for item_id in selection:
            item_index = self.result_tree.index(item_id)
            if 0 <= item_index < len(self.results):
                result = self.results[item_index]
                text += f"{result.get('Titel', 'N/A')} ({result.get('Erscheinungsjahr', 'N/A')})\n"
                text += f"Autoren: {result.get('Autoren', 'N/A')}\n"
                text += f"Journal: {result.get('Journal', 'N/A')}\n"
                text += f"PMID: {result.get('PubMed-ID', 'N/A')}\n"
                text += f"DOI: {result.get('DOI', 'N/A')}\n"
                text += f"URL: {result.get('URL', 'N/A')}\n\n"
        
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            log_message(self.log_widget, "Ausgewählte Einträge in Zwischenablage kopiert.")
    
    def export_results(self, format_type):
        """Exportiert die Ergebnisse in eine Datei."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse zum Exportieren vorhanden.")
            return
        
        # Standarddateiname erstellen
        default_filename = f"PubMed_Ergebnisse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_excel(self.results, file_path, self.log_widget)
                
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_csv(self.results, file_path, self.log_widget)
    
    def show_visualization(self):
        """Zeigt Visualisierungen der Ergebnisdaten an."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse für Visualisierung vorhanden.")
            return
        
        # Neues Fenster für Visualisierungen erstellen
        viz_window = tk.Toplevel(self)
        viz_window.title("PubMed-Ergebnisanalyse")
        viz_window.geometry("800x600")
        viz_window.minsize(600, 400)
        
        notebook = ttk.Notebook(viz_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Jahr-Verteilung
        year_frame = ttk.Frame(notebook)
        notebook.add(year_frame, text="Verteilung nach Jahren")
        
        year_fig = plt.Figure(figsize=(8, 6), dpi=100)
        create_year_distribution_plot(self.results, year_fig)
        
        year_canvas = FigureCanvasTkAgg(year_fig, year_frame)
        year_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Journal-Verteilung
        journal_frame = ttk.Frame(notebook)
        notebook.add(journal_frame, text="Top Journals")
        
        # Journal-Verteilung erstellen
        journal_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = journal_fig.add_subplot(111)
        
        df = pd.DataFrame(self.results)
        # Top 10 Journals ermitteln
        if 'Journal' in df.columns:
            journals = df['Journal'].value_counts().head(10)
            journals.plot(kind='barh', ax=ax)
            ax.set_title('Top 10 Journals')
            ax.set_xlabel('Anzahl der Publikationen')
        else:
            ax.text(0.5, 0.5, "Keine Journal-Daten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        journal_fig.tight_layout()
        
        journal_canvas = FigureCanvasTkAgg(journal_fig, journal_frame)
        journal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Zitatanalyse
        if any(result.get('Zitationsanzahl', 'N/A') != 'N/A' for result in self.results):
            citation_frame = ttk.Frame(notebook)
            notebook.add(citation_frame, text="Zitationsanalyse")
            
            citation_fig = plt.Figure(figsize=(8, 6), dpi=100)
            ax = citation_fig.add_subplot(111)
            
            # Zitationen in numerische Werte umwandeln
            df['Zitationen'] = pd.to_numeric(df['Zitationsanzahl'], errors='coerce')
            df = df.dropna(subset=['Zitationen'])
            
            if not df.empty:
                # Histogramm der Zitationen
                ax.hist(df['Zitationen'], bins=20)
                ax.set_title('Verteilung der Zitationshäufigkeit')
                ax.set_xlabel('Anzahl der Zitationen')
                ax.set_ylabel('Anzahl der Publikationen')
            else:
                ax.text(0.5, 0.5, "Keine Zitationsdaten verfügbar", 
                       ha='center', va='center', transform=ax.transAxes)
            
            citation_fig.tight_layout()
            
            citation_canvas = FigureCanvasTkAgg(citation_fig, citation_frame)
            citation_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

class DNBTab(BaseTab):
    """Tab für die Deutsche Nationalbibliothek-Suche."""
    
    def __init__(self, parent, settings):
        self.connector = DNBConnector(None, settings)  # DNB benötigt keinen API-Key
        super().__init__(parent, settings)
    
    def setup_ui(self):
        """Erstellt die UI für den DNB-Tab."""
        # Hauptframe mit zwei Spalten
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Spalte: Suchoptionen
        left_frame = ttk.LabelFrame(main_frame, text="DNB Suchoptionen")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Rechte Spalte: Ergebnisse und Log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Suchoptionen
        search_form = ttk.Frame(left_frame)
        search_form.pack(fill=tk.X, padx=5, pady=5)
        
        # Suchbegriff
        ttk.Label(search_form, text="Suchbegriff:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.query_entry = ttk.Entry(search_form, width=30)
        self.query_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Suchfeld
        ttk.Label(search_form, text="Suchfeld:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.field_var = tk.StringVar(value="Alle Felder")
        self.field_combo = ttk.Combobox(search_form, textvariable=self.field_var, 
                                         values=self.connector.search_fields, width=28)
        self.field_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zusätzliche Suchbegriffe
        ttk.Label(search_form, text="Zusätzliche Begriffe:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.additional_query_entry = ttk.Entry(search_form, width=30)
        self.additional_query_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zeitraum
        date_frame = ttk.LabelFrame(left_frame, text="Zeitraum")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Von:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, year=2000)
        self.start_date.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(date_frame, text="Bis:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2)
        self.end_date.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # DNB-spezifische Optionen
        dnb_frame = ttk.LabelFrame(left_frame, text="DNB-Optionen")
        dnb_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dnb_frame, text="Dokumenttyp:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.doc_type_var = tk.StringVar(value="")
        self.doc_type_combo = ttk.Combobox(dnb_frame, textvariable=self.doc_type_var, 
                                          values=["", "Buch", "Artikel", "Hochschulschrift", 
                                                "Zeitschrift", "Online-Ressource"], width=28)
        self.doc_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(dnb_frame, text="Sprache:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.language_var = tk.StringVar(value="")
        self.language_combo = ttk.Combobox(dnb_frame, textvariable=self.language_var, 
                                          values=["", "ger", "eng", "fre"], width=28)
        self.language_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(dnb_frame, text="Max. Ergebnisse:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_results_var = tk.StringVar(value="100")
        ttk.Entry(dnb_frame, textvariable=self.max_results_var, width=5).grid(
            row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons für die Suche
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Suchen", command=self.start_search).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset_form).pack(
            side=tk.LEFT, padx=5)
        
        # Ergebnisbereich
        result_frame = ttk.LabelFrame(right_frame, text="DNB-Suchergebnisse")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ergebnistabelle
        columns = ("Titel", "Erscheinungsjahr", "Autoren", "Publisher", "Sprache")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="extended")
        
        # Spaltenüberschriften und -breiten
        self.result_tree.heading("Titel", text="Titel")
        self.result_tree.heading("Erscheinungsjahr", text="Jahr")
        self.result_tree.heading("Autoren", text="Autoren")
        self.result_tree.heading("Publisher", text="Publisher")
        self.result_tree.heading("Sprache", text="Sprache")
        
        self.result_tree.column("Titel", width=300)
        self.result_tree.column("Erscheinungsjahr", width=60, anchor=tk.CENTER)
        self.result_tree.column("Autoren", width=200)
        self.result_tree.column("Publisher", width=150)
        self.result_tree.column("Sprache", width=80, anchor=tk.CENTER)
        
        # Scrollbars für Ergebnistabelle
        tree_scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        tree_scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Anordnung mit Grid für korrekte Scrollbar-Positionierung
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        tree_scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_scroll_x.grid(row=1, column=0, sticky=tk.EW)
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # Rechtsklick-Menü für Ergebnistabelle
        self.context_menu = tk.Menu(self.result_tree, tearoff=0)
        self.context_menu.add_command(label="Details anzeigen", command=self.show_details)
        self.context_menu.add_command(label="In DNB öffnen", command=self.open_dnb_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kopieren", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exportieren (Excel)", command=lambda: self.export_results("excel"))
        self.context_menu.add_command(label="Exportieren (CSV)", command=lambda: self.export_results("csv"))
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        self.result_tree.bind("<Double-1>", lambda e: self.show_details())
        
        # Statusleiste unter der Ergebnistabelle
        status_frame = ttk.Frame(right_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=0)
        
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.result_count_var = tk.StringVar(value="0 Ergebnisse")
        result_count_label = ttk.Label(status_frame, textvariable=self.result_count_var)
        result_count_label.pack(side=tk.RIGHT)
        
        # Export-Buttons
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Nach Excel exportieren", 
                  command=lambda: self.export_results("excel")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Nach CSV exportieren", 
                  command=lambda: self.export_results("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Visualisieren", 
                  command=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Log-Bereich
        log_frame = ttk.Frame(right_frame)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.log_widget = self.create_log_widget(log_frame)
        
        # Ergebnisliste
        self.results = []
    
    def start_search(self):
        """Startet die Suche in der Deutschen Nationalbibliothek."""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Eingabefehler", "Bitte geben Sie einen Suchbegriff ein.")
            return
        
        # Suchanfrage zusammenstellen
        field = self.field_var.get()
        additional_terms = self.additional_query_entry.get().strip()
        date_range = {
            'start': self.start_date.get_date(),
            'end': self.end_date.get_date()
        }
        language = self.language_var.get()
        doc_type = self.doc_type_var.get()
        max_results = int(self.max_results_var.get())
        
        # Zurücksetzen der Ergebnisse und UI
        self.results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_var.set("Suche läuft...")
        log_message(self.log_widget, f"DNB-Suche gestartet: {query}")
        
        # DNB-Query erstellen
        dnb_query = self.connector.construct_query(
            query, additional_terms, date_range, language, doc_type, field)
        
        # Thread für die Suche starten
        threading.Thread(target=self.perform_search, 
                        args=(dnb_query, max_results), 
                        daemon=True).start()
    
    def perform_search(self, query, max_results):
        """Führt die Suche in der DNB durch."""
        try:
            # Suchparameter
            search_params = {
                'name': f"Suche: {self.query_entry.get().strip()}",
                'max_results': max_results
            }
            
            # Suche durchführen
            results = self.connector.search(query, search_params, self.log_widget)
            
            # Ergebnisse anzeigen
            self.after(0, lambda: self.update_results_display(results))
            
        except Exception as e:
            log_message(self.log_widget, f"Fehler bei der DNB-Suche: {e}")
            self.after(0, lambda: self.status_var.set("Fehler bei der Suche"))
    
    def update_results_display(self, results):
        """Aktualisiert die Ergebnisanzeige mit den gefundenen Publikationen."""
        self.results = results
        
        # Tabelle leeren
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # Ergebnisse einfügen
        for i, result in enumerate(self.results):
            self.result_tree.insert("", tk.END, values=(
                result.get("Titel", "N/A"),
                result.get("Erscheinungsjahr", "N/A"),
                result.get("Autoren", "N/A"),
                result.get("Publisher", "N/A"),
                result.get("Sprache", "N/A")
            ))
            
        # Status aktualisieren
        self.status_var.set("Suche abgeschlossen")
        self.result_count_var.set(f"{len(self.results)} Ergebnisse")
        
        log_message(self.log_widget, f"DNB-Suche abgeschlossen. {len(self.results)} Ergebnisse gefunden.")
        
        # Globale Ergebnisliste aktualisieren
        global search_results
        search_results = self.results
    
    def reset_form(self):
        """Setzt das Formular zurück."""
        self.query_entry.delete(0, tk.END)
        self.additional_query_entry.delete(0, tk.END)
        self.field_var.set("Alle Felder")
        self.start_date.set_date(datetime(2000, 1, 1).date())
        self.end_date.set_date(datetime.now().date())
        self.doc_type_var.set("")
        self.language_var.set("")
        self.max_results_var.set("100")
    
    def show_context_menu(self, event):
        """Zeigt das Kontextmenü für die Ergebnistabelle an."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_details(self):
        """Zeigt Details für den ausgewählten Eintrag an."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        
        # Details-Dialog anzeigen
        details_window = tk.Toplevel(self)
        details_window.title("DNB-Publikationsdetails")
        details_window.geometry("600x400")
        details_window.minsize(600, 400)
        
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbare Textansicht für die Details
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scroll.config(command=text.yview)
        
        # Details einfügen
        text.insert(tk.END, f"Titel: {result.get('Titel', 'N/A')}\n\n")
        text.insert(tk.END, f"Autoren: {result.get('Autoren', 'N/A')}\n\n")
        text.insert(tk.END, f"Erscheinungsjahr: {result.get('Erscheinungsjahr', 'N/A')}\n\n")
        text.insert(tk.END, f"Publisher: {result.get('Publisher', 'N/A')}\n\n")
        text.insert(tk.END, f"Sprache: {result.get('Sprache', 'N/A')}\n\n")
        text.insert(tk.END, f"Dokumenttyp: {result.get('Dokumenttyp', 'N/A')}\n\n")
        text.insert(tk.END, f"Identifier: {result.get('Identifier', 'N/A')}\n\n")
        text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
        
        # Text als schreibgeschützt markieren
        text.config(state=tk.DISABLED)
        
        # Button zum Schließen und URL öffnen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Schließen", 
                  command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
                  
        if result.get('URL') and result.get('URL') != 'N/A':
            ttk.Button(button_frame, text="In DNB öffnen", 
                      command=lambda: self.open_url(result.get('URL'))).pack(side=tk.RIGHT, padx=5)
    
    def open_dnb_url(self):
        """Öffnet die DNB-URL für den ausgewählten Eintrag."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        if result.get('URL') and result.get('URL') != 'N/A':
            self.open_url(result.get('URL'))
    
    def open_url(self, url):
        """Öffnet eine URL im Standardbrowser."""
        import webbrowser
        try:
            webbrowser.open(url)
            log_message(self.log_widget, f"URL geöffnet: {url}")
        except Exception as e:
            log_message(self.log_widget, f"Fehler beim Öffnen der URL: {e}")
    
    def copy_selected(self):
        """Kopiert ausgewählte Einträge in die Zwischenablage."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        text = ""
        for item_id in selection:
            item_index = self.result_tree.index(item_id)
            if 0 <= item_index < len(self.results):
                result = self.results[item_index]
                text += f"{result.get('Titel', 'N/A')} ({result.get('Erscheinungsjahr', 'N/A')})\n"
                text += f"Autoren: {result.get('Autoren', 'N/A')}\n"
                text += f"Publisher: {result.get('Publisher', 'N/A')}\n"
                text += f"Sprache: {result.get('Sprache', 'N/A')}\n"
                text += f"URL: {result.get('URL', 'N/A')}\n\n"
        
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            log_message(self.log_widget, "Ausgewählte Einträge in Zwischenablage kopiert.")
    
    def export_results(self, format_type):
        """Exportiert die Ergebnisse in eine Datei."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse zum Exportieren vorhanden.")
            return
        
        # Standarddateiname erstellen
        default_filename = f"DNB_Ergebnisse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_excel(self.results, file_path, self.log_widget)
                
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_csv(self.results, file_path, self.log_widget)
    
    def show_visualization(self):
        """Zeigt Visualisierungen der Ergebnisdaten an."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse für Visualisierung vorhanden.")
            return
        
        # Neues Fenster für Visualisierungen erstellen
        viz_window = tk.Toplevel(self)
        viz_window.title("DNB-Ergebnisanalyse")
        viz_window.geometry("800x600")
        viz_window.minsize(600, 400)
        
        notebook = ttk.Notebook(viz_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Jahr-Verteilung
        year_frame = ttk.Frame(notebook)
        notebook.add(year_frame, text="Verteilung nach Jahren")
        
        year_fig = plt.Figure(figsize=(8, 6), dpi=100)
        create_year_distribution_plot(self.results, year_fig)
        
        year_canvas = FigureCanvasTkAgg(year_fig, year_frame)
        year_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Sprach-Verteilung
        language_frame = ttk.Frame(notebook)
        notebook.add(language_frame, text="Sprachen")
        
        # Sprach-Verteilung erstellen
        language_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = language_fig.add_subplot(111)
        
        df = pd.DataFrame(self.results)
        if 'Sprache' in df.columns:
            languages = df['Sprache'].value_counts()
            languages.plot(kind='pie', ax=ax, autopct='%1.1f%%')
            ax.set_title('Verteilung nach Sprachen')
            ax.set_ylabel('')  # Entferne y-Label
        else:
            ax.text(0.5, 0.5, "Keine Sprachdaten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        language_fig.tight_layout()
        
        language_canvas = FigureCanvasTkAgg(language_fig, language_frame)
        language_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Publisher-Verteilung
        publisher_frame = ttk.Frame(notebook)
        notebook.add(publisher_frame, text="Top Publisher")
        
        # Publisher-Verteilung erstellen
        publisher_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = publisher_fig.add_subplot(111)
        
        if 'Publisher' in df.columns:
            publishers = df['Publisher'].value_counts().head(10)
            publishers.plot(kind='barh', ax=ax)
            ax.set_title('Top 10 Publisher')
            ax.set_xlabel('Anzahl der Publikationen')
        else:
            ax.text(0.5, 0.5, "Keine Publisher-Daten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        publisher_fig.tight_layout()
        
        publisher_canvas = FigureCanvasTkAgg(publisher_fig, publisher_frame)
        publisher_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

class WoSTab(BaseTab):
    """Tab für die Web of Science-Suche."""
    
    def __init__(self, parent, settings):
        self.connector = WoSConnector(settings.get('wos_api_key', ''), settings)
        super().__init__(parent, settings)
    
    def setup_ui(self):
        """Erstellt die UI für den Web of Science-Tab."""
        # Hauptframe mit zwei Spalten
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Spalte: Suchoptionen
        left_frame = ttk.LabelFrame(main_frame, text="Web of Science Suchoptionen")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Rechte Spalte: Ergebnisse und Log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Suchoptionen
        search_form = ttk.Frame(left_frame)
        search_form.pack(fill=tk.X, padx=5, pady=5)
        
        # Suchbegriff
        ttk.Label(search_form, text="Suchbegriff:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.query_entry = ttk.Entry(search_form, width=30)
        self.query_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Suchfeld
        ttk.Label(search_form, text="Suchfeld:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.field_var = tk.StringVar(value="Alle Felder")
        self.field_combo = ttk.Combobox(search_form, textvariable=self.field_var, 
                                       values=self.connector.search_fields, width=28)
        self.field_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zusätzliche Suchbegriffe
        ttk.Label(search_form, text="Zusätzliche Begriffe:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.additional_query_entry = ttk.Entry(search_form, width=30)
        self.additional_query_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Zeitraum
        date_frame = ttk.LabelFrame(left_frame, text="Zeitraum")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Von:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, year=2000)
        self.start_date.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(date_frame, text="Bis:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # WoS spezifische Optionen
        wos_frame = ttk.LabelFrame(left_frame, text="WoS-Optionen")
        wos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(wos_frame, text="Publikationstyp:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.pub_type_var = tk.StringVar(value="")
        self.pub_type_combo = ttk.Combobox(wos_frame, textvariable=self.pub_type_var, 
                                          values=["", "Article", "Review", "Proceedings Paper", 
                                                 "Book", "Book Chapter"], width=28)
        self.pub_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(wos_frame, text="Sprache:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.language_var = tk.StringVar(value="")
        self.language_combo = ttk.Combobox(wos_frame, textvariable=self.language_var, 
                                          values=["", "English", "German", "French"], width=28)
        self.language_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        
        ttk.Label(wos_frame, text="Max. Ergebnisse:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_results_var = tk.StringVar(value="100")
        ttk.Entry(wos_frame, textvariable=self.max_results_var, width=5).grid(
            row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Buttons für die Suche
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Suchen", command=self.start_search).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset_form).pack(
            side=tk.LEFT, padx=5)
        
        # API-Key-Status
        api_frame = ttk.Frame(left_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.api_status_var = tk.StringVar(value="API-Key: " + 
                                          ("Vorhanden" if self.settings.get('wos_api_key') 
                                           else "Nicht konfiguriert - Dummy-Modus aktiv"))
        ttk.Label(api_frame, textvariable=self.api_status_var).pack(side=tk.LEFT)
        ttk.Button(api_frame, text="Konfigurieren", 
                  command=self.configure_api_key).pack(side=tk.RIGHT, padx=5)
        
        # Ergebnisbereich
        result_frame = ttk.LabelFrame(right_frame, text="WoS-Suchergebnisse")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Ergebnistabelle
        columns = ("Titel", "Erscheinungsjahr", "Autoren", "Journal", "Zitationen", "WoS-ID")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="extended")
        
        # Spaltenüberschriften und -breiten
        self.result_tree.heading("Titel", text="Titel")
        self.result_tree.heading("Erscheinungsjahr", text="Jahr")
        self.result_tree.heading("Autoren", text="Autoren")
        self.result_tree.heading("Journal", text="Journal")
        self.result_tree.heading("Zitationen", text="Zitationen")
        self.result_tree.heading("WoS-ID", text="WoS-ID")
        
        self.result_tree.column("Titel", width=300)
        self.result_tree.column("Erscheinungsjahr", width=60, anchor=tk.CENTER)
        self.result_tree.column("Autoren", width=200)
        self.result_tree.column("Journal", width=150)
        self.result_tree.column("Zitationen", width=80, anchor=tk.CENTER)
        self.result_tree.column("WoS-ID", width=120, anchor=tk.CENTER)
        
        # Scrollbars für Ergebnistabelle
        tree_scroll_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        tree_scroll_x = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Anordnung mit Grid für korrekte Scrollbar-Positionierung
        self.result_tree.grid(row=0, column=0, sticky=tk.NSEW)
        tree_scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_scroll_x.grid(row=1, column=0, sticky=tk.EW)
        
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # Rechtsklick-Menü für Ergebnistabelle
        self.context_menu = tk.Menu(self.result_tree, tearoff=0)
        self.context_menu.add_command(label="Details anzeigen", command=self.show_details)
        self.context_menu.add_command(label="In WoS öffnen", command=self.open_wos_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kopieren", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exportieren (Excel)", command=lambda: self.export_results("excel"))
        self.context_menu.add_command(label="Exportieren (CSV)", command=lambda: self.export_results("csv"))
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        self.result_tree.bind("<Double-1>", lambda e: self.show_details())
        
        # Statusleiste unter der Ergebnistabelle
        status_frame = ttk.Frame(right_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=0)
        
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.result_count_var = tk.StringVar(value="0 Ergebnisse")
        result_count_label = ttk.Label(status_frame, textvariable=self.result_count_var)
        result_count_label.pack(side=tk.RIGHT)
        
        # Export-Buttons
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Nach Excel exportieren", 
                  command=lambda: self.export_results("excel")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Nach CSV exportieren", 
                  command=lambda: self.export_results("csv")).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Visualisieren", 
                  command=self.show_visualization).pack(side=tk.LEFT, padx=5)
        
        # Log-Bereich
        log_frame = ttk.Frame(right_frame)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.log_widget = self.create_log_widget(log_frame)
        
        # Ergebnisliste
        self.results = []
    
    def configure_api_key(self):
        """Konfiguriert den WoS API-Key."""
        current_key = self.settings.get('wos_api_key', '')
        api_key = simpledialog.askstring("API-Key konfigurieren", 
                                       "Geben Sie Ihren Web of Science API-Key ein:",
                                       initialvalue=current_key)
        
        if api_key is not None:  # Nicht abgebrochen
            self.settings['wos_api_key'] = api_key
            save_settings(self.settings)
            
            # Connector aktualisieren
            self.connector = WoSConnector(api_key, self.settings)
            
            # Status aktualisieren
            dummy_text = " - Dummy-Modus aktiv" if not api_key else ""
            self.api_status_var.set("API-Key: " + ("Vorhanden" if api_key else "Nicht konfiguriert") + dummy_text)
            
            log_message(self.log_widget, "Web of Science API-Key wurde aktualisiert.")
    
    def start_search(self):
        """Startet die Suche in Web of Science."""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Eingabefehler", "Bitte geben Sie einen Suchbegriff ein.")
            return
        
        # Suchanfrage zusammenstellen
        field = self.field_var.get()
        additional_terms = self.additional_query_entry.get().strip()
        date_range = {
            'start': self.start_date.get_date(),
            'end': self.end_date.get_date()
        }
        language = self.language_var.get()
        pub_type = self.pub_type_var.get()
        max_results = int(self.max_results_var.get())
        
        # Zurücksetzen der Ergebnisse und UI
        self.results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_var.set("Suche läuft...")
        log_message(self.log_widget, f"WoS-Suche gestartet: {query}")
        
        # WoS-Query erstellen
        wos_query = self.connector.construct_query(
            query, additional_terms, date_range, language, pub_type, field)
        
        # Thread für die Suche starten
        threading.Thread(target=self.perform_search, 
                        args=(wos_query, max_results), 
                        daemon=True).start()
    
    def perform_search(self, query, max_results):
        """Führt die Suche in Web of Science durch."""
        try:
            # Suchparameter
            search_params = {
                'name': f"Suche: {self.query_entry.get().strip()}",
                'max_results': max_results
            }
            
            # Suche durchführen
            results = self.connector.search(query, search_params, self.log_widget)
            
            # Ergebnisse anzeigen
            self.after(0, lambda: self.update_results_display(results))
            
        except Exception as e:
            log_message(self.log_widget, f"Fehler bei der WoS-Suche: {e}")
            self.after(0, lambda: self.status_var.set("Fehler bei der Suche"))
    
    def update_results_display(self, results):
        """Aktualisiert die Ergebnisanzeige mit den gefundenen Publikationen."""
        self.results = results
        
        # Tabelle leeren
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # Ergebnisse einfügen
        for i, result in enumerate(self.results):
            self.result_tree.insert("", tk.END, values=(
                result.get("Titel", "N/A"),
                result.get("Erscheinungsjahr", "N/A"),
                result.get("Autoren", "N/A"),
                result.get("Journal", "N/A"),
                result.get("Zitationsanzahl", "N/A"),
                result.get("WoS-ID", "N/A")
            ))
            
        # Status aktualisieren
        self.status_var.set("Suche abgeschlossen")
        self.result_count_var.set(f"{len(self.results)} Ergebnisse")
        
        log_message(self.log_widget, f"WoS-Suche abgeschlossen. {len(self.results)} Ergebnisse gefunden.")
        
        # Globale Ergebnisliste aktualisieren
        global search_results
        search_results = self.results
    
    def reset_form(self):
        """Setzt das Formular zurück."""
        self.query_entry.delete(0, tk.END)
        self.additional_query_entry.delete(0, tk.END)
        self.field_var.set("Alle Felder")
        self.start_date.set_date(datetime(2000, 1, 1).date())
        self.end_date.set_date(datetime.now().date())
        self.pub_type_var.set("")
        self.language_var.set("")
        self.max_results_var.set("100")
    
    def show_context_menu(self, event):
        """Zeigt das Kontextmenü für die Ergebnistabelle an."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_details(self):
        """Zeigt Details für den ausgewählten Eintrag an."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        
        # Details-Dialog anzeigen
        details_window = tk.Toplevel(self)
        details_window.title("WoS-Publikationsdetails")
        details_window.geometry("600x400")
        details_window.minsize(600, 400)
        
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbare Textansicht für die Details
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scroll.config(command=text.yview)
        
        # Details einfügen
        text.insert(tk.END, f"Titel: {result.get('Titel', 'N/A')}\n\n")
        text.insert(tk.END, f"Autoren: {result.get('Autoren', 'N/A')}\n\n")
        text.insert(tk.END, f"Erscheinungsjahr: {result.get('Erscheinungsjahr', 'N/A')}\n\n")
        text.insert(tk.END, f"Journal: {result.get('Journal', 'N/A')}\n\n")
        text.insert(tk.END, f"DOI: {result.get('DOI', 'N/A')}\n\n")
        text.insert(tk.END, f"Zitationsanzahl: {result.get('Zitationsanzahl', 'N/A')}\n\n")
        text.insert(tk.END, f"WoS-ID: {result.get('WoS-ID', 'N/A')}\n\n")
        text.insert(tk.END, f"URL: {result.get('URL', 'N/A')}\n\n")
        
        # Text als schreibgeschützt markieren
        text.config(state=tk.DISABLED)
        
        # Button zum Schließen und URL öffnen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Schließen", 
                  command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
                  
        if result.get('URL') and result.get('URL') != 'N/A':
            ttk.Button(button_frame, text="In WoS öffnen", 
                      command=lambda: self.open_url(result.get('URL'))).pack(side=tk.RIGHT, padx=5)
    
    def open_wos_url(self):
        """Öffnet die WoS-URL für den ausgewählten Eintrag."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item_index = self.result_tree.index(item_id)
        
        if item_index < 0 or item_index >= len(self.results):
            return
        
        result = self.results[item_index]
        if result.get('URL') and result.get('URL') != 'N/A':
            self.open_url(result.get('URL'))
    
    def open_url(self, url):
        """Öffnet eine URL im Standardbrowser."""
        import webbrowser
        try:
            webbrowser.open(url)
            log_message(self.log_widget, f"URL geöffnet: {url}")
        except Exception as e:
            log_message(self.log_widget, f"Fehler beim Öffnen der URL: {e}")
    
    def copy_selected(self):
        """Kopiert ausgewählte Einträge in die Zwischenablage."""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        text = ""
        for item_id in selection:
            item_index = self.result_tree.index(item_id)
            if 0 <= item_index < len(self.results):
                result = self.results[item_index]
                text += f"{result.get('Titel', 'N/A')} ({result.get('Erscheinungsjahr', 'N/A')})\n"
                text += f"Autoren: {result.get('Autoren', 'N/A')}\n"
                text += f"Journal: {result.get('Journal', 'N/A')}\n"
                text += f"Zitationen: {result.get('Zitationsanzahl', 'N/A')}\n"
                text += f"WoS-ID: {result.get('WoS-ID', 'N/A')}\n"
                text += f"URL: {result.get('URL', 'N/A')}\n\n"
        
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            log_message(self.log_widget, "Ausgewählte Einträge in Zwischenablage kopiert.")
    
    def export_results(self, format_type):
        """Exportiert die Ergebnisse in eine Datei."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse zum Exportieren vorhanden.")
            return
        
        # Standarddateiname erstellen
        default_filename = f"WoS_Ergebnisse_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == "excel":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_excel(self.results, file_path, self.log_widget)
                
        elif format_type == "csv":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                initialfile=default_filename
            )
            if file_path:
                export_to_csv(self.results, file_path, self.log_widget)
    
    def show_visualization(self):
        """Zeigt Visualisierungen der Ergebnisdaten an."""
        if not self.results:
            messagebox.showinfo("Information", "Keine Ergebnisse für Visualisierung vorhanden.")
            return
        
        # Neues Fenster für Visualisierungen erstellen
        viz_window = tk.Toplevel(self)
        viz_window.title("WoS-Ergebnisanalyse")
        viz_window.geometry("800x600")
        viz_window.minsize(600, 400)
        
        notebook = ttk.Notebook(viz_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Jahr-Verteilung
        year_frame = ttk.Frame(notebook)
        notebook.add(year_frame, text="Verteilung nach Jahren")
        
        year_fig = plt.Figure(figsize=(8, 6), dpi=100)
        create_year_distribution_plot(self.results, year_fig)
        
        year_canvas = FigureCanvasTkAgg(year_fig, year_frame)
        year_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Journal-Verteilung
        journal_frame = ttk.Frame(notebook)
        notebook.add(journal_frame, text="Top Journals")
        
        # Journal-Verteilung erstellen
        journal_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = journal_fig.add_subplot(111)
        
        df = pd.DataFrame(self.results)
        # Top 10 Journals ermitteln
        if 'Journal' in df.columns:
            journals = df['Journal'].value_counts().head(10)
            journals.plot(kind='barh', ax=ax)
            ax.set_title('Top 10 Journals')
            ax.set_xlabel('Anzahl der Publikationen')
        else:
            ax.text(0.5, 0.5, "Keine Journal-Daten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        journal_fig.tight_layout()
        
        journal_canvas = FigureCanvasTkAgg(journal_fig, journal_frame)
        journal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Zitatanalyse
        citation_frame = ttk.Frame(notebook)
        notebook.add(citation_frame, text="Zitationsanalyse")
        
        citation_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = citation_fig.add_subplot(111)
        
        if 'Zitationsanzahl' in df.columns:
            # Zitationen in numerische Werte umwandeln
            df['Zitationen'] = pd.to_numeric(df['Zitationsanzahl'], errors='coerce')
            df = df.dropna(subset=['Zitationen'])
            
            if not df.empty:
                # Histogramm der Zitationen
                ax.hist(df['Zitationen'], bins=min(20, len(df['Zitationen'].unique())), color='skyblue', edgecolor='black')
                ax.set_title('Verteilung der Zitationshäufigkeit')
                ax.set_xlabel('Anzahl der Zitationen')
                ax.set_ylabel('Anzahl der Publikationen')
                
                # Mittelwert anzeigen
                mean_citations = df['Zitationen'].mean()
                median_citations = df['Zitationen'].median()
                ax.axvline(mean_citations, color='red', linestyle='dashed', linewidth=1)
                ax.text(mean_citations*1.1, ax.get_ylim()[1]*0.9, f'Mittelwert: {mean_citations:.1f}', color='red')
                ax.axvline(median_citations, color='green', linestyle='dashed', linewidth=1)
                ax.text(median_citations*1.1, ax.get_ylim()[1]*0.8, f'Median: {median_citations:.1f}', color='green')
            else:
                ax.text(0.5, 0.5, "Keine numerischen Zitationsdaten verfügbar", 
                       ha='center', va='center', transform=ax.transAxes)
        else:
            ax.text(0.5, 0.5, "Keine Zitationsdaten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        citation_fig.tight_layout()
        
        citation_canvas = FigureCanvasTkAgg(citation_fig, citation_frame)
        citation_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Impact-Factor-Analyse (falls vorhanden)
        if any(result.get('Impact-Factor', 'N/A') != 'N/A' for result in self.results):
            impact_frame = ttk.Frame(notebook)
            notebook.add(impact_frame, text="Impact Factor")
            
            impact_fig = plt.Figure(figsize=(8, 6), dpi=100)
            ax = impact_fig.add_subplot(111)
            
            # Impact Faktoren extrahieren
            if 'Impact-Factor' in df.columns:
                df['IF'] = pd.to_numeric(df['Impact-Factor'], errors='coerce')
                df = df.dropna(subset=['IF'])
                
                if not df.empty:
                    # Scatterplot: Jahr vs. Impact Factor
                    df['Jahr'] = pd.to_numeric(df['Erscheinungsjahr'], errors='coerce')
                    df = df.dropna(subset=['Jahr'])
                    
                    scatter = ax.scatter(df['Jahr'], df['IF'], alpha=0.6, s=30)
                    ax.set_title('Impact Factor nach Erscheinungsjahr')
                    ax.set_xlabel('Erscheinungsjahr')
                    ax.set_ylabel('Impact Factor')
                    
                    # Trendlinie
                    if len(df) > 1:
                        z = np.polyfit(df['Jahr'], df['IF'], 1)
                        p = np.poly1d(z)
                        years = sorted(df['Jahr'].unique())
                        if len(years) > 1:
                            ax.plot(years, p(years), "r--", alpha=0.8)
                            ax.text(0.05, 0.95, f'Trend: {z[0]:.4f}x + {z[1]:.2f}', 
                                   transform=ax.transAxes, fontsize=10, 
                                   verticalalignment='top')
                else:
                    ax.text(0.5, 0.5, "Keine numerischen Impact Factor-Daten verfügbar", 
                           ha='center', va='center', transform=ax.transAxes)
            else:
                ax.text(0.5, 0.5, "Keine Impact Factor-Daten verfügbar", 
                       ha='center', va='center', transform=ax.transAxes)
            
            impact_fig.tight_layout()
            
            impact_canvas = FigureCanvasTkAgg(impact_fig, impact_frame)
            impact_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        # Autoren-Netzwerk-Analyse
        authors_frame = ttk.Frame(notebook)
        notebook.add(authors_frame, text="Autoren-Netzwerk")
        
        authors_fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = authors_fig.add_subplot(111)
        
        # Autoren extrahieren und zählen
        all_authors = []
        for result in self.results:
            authors = result.get('Autoren', '')
            if authors and authors != 'N/A':
                author_list = [a.strip() for a in authors.split(',')]
                all_authors.extend(author_list)
        
        if all_authors:
            author_counts = {}
            for author in all_authors:
                if author in author_counts:
                    author_counts[author] += 1
                else:
                    author_counts[author] = 1
            
            # Top-Autoren filtern
            top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            authors = [x[0] for x in top_authors]
            counts = [x[1] for x in top_authors]
            
            # Horizontales Balkendiagramm
            y_pos = np.arange(len(authors))
            ax.barh(y_pos, counts, align='center')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(authors)
            ax.invert_yaxis()  # Labels von oben nach unten
            ax.set_xlabel('Anzahl der Publikationen')
            ax.set_title('Top 15 Autoren nach Anzahl der Publikationen')
        else:
            ax.text(0.5, 0.5, "Keine Autoren-Daten verfügbar", 
                   ha='center', va='center', transform=ax.transAxes)
        
        authors_fig.tight_layout()
        
        authors_canvas = FigureCanvasTkAgg(authors_fig, authors_frame)
        authors_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Hilfsfunktionen für die Visualisierung

def create_year_distribution_plot(results, fig):
    """Erstellt ein Balkendiagramm für die Verteilung der Publikationen nach Jahren."""
    ax = fig.add_subplot(111)
    
    # Jahre aus den Ergebnissen extrahieren
    years = []
    for result in results:
        year = result.get('Erscheinungsjahr', 'N/A')
        if year != 'N/A':
            try:
                years.append(int(year))
            except (ValueError, TypeError):
                pass
    
    if years:
        # Häufigkeitszählung
        year_counts = {}
        for year in years:
            if year in year_counts:
                year_counts[year] += 1
            else:
                year_counts[year] = 1
        
        # Sortierte Liste der Jahre
        sorted_years = sorted(year_counts.keys())
        counts = [year_counts[year] for year in sorted_years]
        
        # Balkendiagramm erstellen
        bars = ax.bar(sorted_years, counts)
        
        # Labels und Titel
        ax.set_xlabel('Jahr')
        ax.set_ylabel('Anzahl der Publikationen')
        ax.set_title('Verteilung der Publikationen nach Jahren')
        
        # Achsenbeschriftung optimieren
        if sorted_years:
            min_year = min(sorted_years)
            max_year = max(sorted_years)
            year_range = max_year - min_year
            step = max(1, year_range // 10)  # Mindestens jedes Jahr, sonst etwa 10 Labels
            ax.set_xticks(range(min_year, max_year + 1, step))
        
        # Werte über den Balken anzeigen
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}',
                      xy=(bar.get_x() + bar.get_width() / 2, height),
                      xytext=(0, 3),  # 3 Punkte über der Balkenhöhe
                      textcoords="offset points",
                      ha='center', va='bottom')
    else:
        ax.text(0.5, 0.5, "Keine Jahresdaten verfügbar", 
               ha='center', va='center', transform=ax.transAxes)
    
    fig.tight_layout()

# Hilfsfunktionen für den Export

def export_to_excel(results, file_path, log_widget=None):
    """Exportiert die Ergebnisse nach Excel."""
    try:
        # DataFrame erstellen
        df = pd.DataFrame(results)
        
        # In Excel exportieren
        df.to_excel(file_path, index=False)
        
        if log_widget:
            log_message(log_widget, f"Ergebnisse erfolgreich nach Excel exportiert: {file_path}")
        
        return True
    except Exception as e:
        if log_widget:
            log_message(log_widget, f"Fehler beim Export nach Excel: {e}")
        messagebox.showerror("Exportfehler", f"Fehler beim Export nach Excel:\n{e}")
        return False

def export_to_csv(results, file_path, log_widget=None):
    """Exportiert die Ergebnisse nach CSV."""
    try:
        # DataFrame erstellen
        df = pd.DataFrame(results)
        
        # In CSV exportieren
        df.to_csv(file_path, index=False, encoding='utf-8-sig')  # UTF-8 mit BOM für Excel-Kompatibilität
        
        if log_widget:
            log_message(log_widget, f"Ergebnisse erfolgreich nach CSV exportiert: {file_path}")
        
        return True
    except Exception as e:
        if log_widget:
            log_message(log_widget, f"Fehler beim Export nach CSV: {e}")
        messagebox.showerror("Exportfehler", f"Fehler beim Export nach CSV:\n{e}")
        return False

# Hauptfunktion für den Programmstart

def create_settings_dir():
    """Erstellt ein Verzeichnis für die Einstellungen der Anwendung, falls es nicht existiert."""
    import os
    
    # Typischer Pfad für Einstellungen
    settings_dir = os.path.join(os.path.expanduser("~"), ".medical_spytool")
    
    # Verzeichnis erstellen, falls es nicht existiert
    if not os.path.exists(settings_dir):
        try:
            os.makedirs(settings_dir)
            print(f"Einstellungsverzeichnis erstellt: {settings_dir}")
        except Exception as e:
            print(f"Fehler beim Erstellen des Einstellungsverzeichnisses: {e}")
    
    return settings_dir

def show_welcome_dialog(root, settings):
    """Zeigt einen Willkommensdialog beim ersten Start der Anwendung an."""
    import tkinter as tk
    from tkinter import messagebox
    
    # Prüfen, ob es der erste Start ist
    first_run = settings.get("first_run", True)
    
    if first_run:
        welcome_text = """
        Willkommen beim MedicalSpyTool!
        
        Diese Anwendung unterstützt Sie bei der Verwaltung medizinischer Daten.
        
        Bitte beachten Sie die Datenschutzrichtlinien und stellen Sie sicher, 
        dass alle sensiblen Patientendaten gemäß den geltenden Vorschriften 
        behandelt werden.
        """
        
        messagebox.showinfo("Willkommen", welcome_text)
        
        # Ersten Start auf False setzen für zukünftige Starts
        settings["first_run"] = False
        save_settings(settings)
    
    return True

def save_settings(settings):
    """Speichert die Anwendungseinstellungen."""
    import json
    import os
    import logging
    
    logger = logging.getLogger("MedicalSpyTool")
    
    settings_dir = os.path.join(os.path.expanduser("~"), ".medical_spytool")
    settings_file = os.path.join(settings_dir, "settings.json")
    
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        logger.info("Einstellungen gespeichert.")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Einstellungen: {e}")

def run_app():
    """Startet die Anwendung."""
    # Sicherstellen, dass Settings-Datei und -Verzeichnis existieren
    create_settings_dir()
    settings = load_settings()
    
    # Fenster erstellen und anzeigen
    root = tk.Tk()
    root.title("BiblioRecherchetool v1.0")
    
    # Icon setzen
    try:
        # Versuche das Icon zu setzen
        root.iconbitmap("assets/icon.ico")
    except:
        pass  # Falls kein Icon vorhanden ist, ignorieren
    
    # Fenstergröße und Positionierung
    window_width = 1024
    window_height = 768
    
    # Bildschirmabmessungen abrufen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Mittelpunkt berechnen
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    
    # Fenstergröße und -position setzen
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.minsize(800, 600)
    
    # Wenn Settings leer sind, zeige einen Willkommens-Dialog
    if not settings.get('setup_done', False):
        show_welcome_dialog(root, settings)
    
    # Hauptanwendung erstellen
    app = Application(root, settings)
    
    # Anwendung starten
    root.mainloop()

if __name__ == "__main__":
    run_app()
