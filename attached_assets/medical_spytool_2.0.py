#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Erweitertes wissenschaftliches Publikations-Suchtool
Version 2.0

Dieses Skript bietet eine umfassende GUI-Anwendung zur Suche in verschiedenen wissenschaftlichen 
und medizinischen Datenbanken, darunter PubMed und die Deutsche Nationalbibliothek (DNB).
Es kombiniert die Funktionalität mehrerer vorheriger Tools und bietet eine konsistente Oberfläche
für alle unterstützten Datenbanken mit erweiterten Such-, Analyse- und Exportfunktionen.
"""

####
# Imports und globale Einstellungen
####
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
from functools import lru_cache
import logging
import re
import sys

# Konfigurationsdatei
config_file = "medicalspy_config.json"

# Globale Variablen
persons = []    # Liste der Personen (jeder Eintrag ist ein Dictionary)
editing_person_index = None
search_results = []    # Gesammelte Suchergebnisse (Liste von Dictionaries)
settings = {}    # Einstellungen aus der Config-Datei
global_log = []    # Globaler Log (Liste von Logeinträgen)

# Datei für gespeicherte Suchanfragen
saved_queries_file = "saved_queries.json"

# Konfigurieren des Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medicalspy.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MedicalSpy")

# DNB Namespace-Dictionary
dnb_ns = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/'
}

####
# Einstellungen laden und speichern
####
def load_settings():
    global settings
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
        logger.info("Einstellungen geladen.")
    except FileNotFoundError:
        settings = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "pubmed_api_key": "",
            "output_columns": [
                "Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", 
                "URL", "Autoren", "Veröffentlichungsjahr", "Zitationsanzahl"
            ],
            "default_database": "PubMed"
        }
        save_settings()
        logger.info("Standard-Einstellungen erstellt.")
    return settings

def save_settings():
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
    logger.info("Einstellungen gespeichert.")

####
# Logging-Funktionen (GUI und Konsole)
####
def log_message(log_widget, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    global_log.append(full_msg)
    logger.info(message)
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

####
# Funktionen für gespeicherte Suchanfragen
####
def load_saved_queries():
    try:
        with open(saved_queries_file, "r", encoding="utf-8") as f:
            queries = json.load(f)
        logger.info("Gespeicherte Suchanfragen geladen.")
        return queries
    except FileNotFoundError:
        logger.info("Keine gespeicherten Suchanfragen gefunden. Erstelle leere Liste.")
        return []
    except Exception as e:
        logger.error(f"Fehler beim Laden der gespeicherten Suchanfragen: {e}")
        return []

def save_saved_queries(queries):
    try:
        with open(saved_queries_file, "w", encoding="utf-8") as f:
            json.dump(queries, f, indent=4)
        logger.info("Gespeicherte Suchanfragen gespeichert.")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Suchanfragen: {e}")

####
# Datenbank-Connector-Klassen
####
class DatabaseConnector:
    """Basisklasse für Datenbankverbindungen"""
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Generic Database"
        self.max_results_per_page = 100
        self.search_fields = []
        
    def search(self, query, params=None):
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
        
    def get_max_results_per_page(self):
        """Gibt die maximale Anzahl von Ergebnissen pro Seite zurück"""
        return self.max_results_per_page
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                       language=None, pub_type=None, field=None):
        """Standard-Implementierung für den Aufbau einer Abfrage. Kann in Unterklassen überschrieben werden."""
        query = base_query
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
        # Datum, Sprache und Publikationstyp werden in spezifischen Unterklassen hinzugefügt
        return query

class DNBConnector(DatabaseConnector):
    """Connector für die Deutsche Nationalbibliothek"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Deutsche Nationalbibliothek"
        self.max_results_per_page = 1000
        self.search_fields = ["Alle Felder", "Titel", "Autor", "Schlagwort", "Jahr"]
        self.base_url = "https://services.dnb.de/sru/dnb"
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                       language=None, pub_type=None, field=None):
        """Baut eine CQL-Anfrage für die DNB"""
        # Transformiere den Suchbegriff für DNB-Format
        query = self.transform_query(base_query)
        
        # Füge zusätzliche Suchbegriffe hinzu
        if additional_terms:
            additional_terms = self.transform_query(additional_terms)
            query = f"({query}) AND ({additional_terms})"
            
        # Füge Datumsbereich hinzu, wenn vorhanden
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].replace("-", "/")
            end_date = date_range['end'].replace("-", "/")
            query += f" AND (\"{start_date}\"[Date - Publication] : \"{end_date}\"[Date - Publication])"
            
        # Füge Sprache hinzu, wenn vorhanden
        if language:
            query += f" AND language={language}"
            
        return query
        
    def transform_query(self, search_term):
        """Transformiert einen Suchbegriff in das CQL-Format für DNB"""
        if not search_term.lower().startswith("dc.any"):
            parts = search_term.split()
            if len(parts) == 2:
                return f'dc.any all ("{search_term}" or "{parts[1]}, {parts[0]}")'
            else:
                return f'dc.any all "{search_term}"'
        return search_term
        
    def search(self, query, params=None):
        """Sucht in der DNB nach Publikationen"""
        logger.info(f"DNB-Suche: {query}")
        all_results = []
        start_record = 1
        total_records = None
        
        # Default Parameter wenn nicht angegeben
        if params is None:
            params = {}
        
        page_size = params.get('page_size', self.max_results_per_page)
        
        while True:
            try:
                # Sende Anfrage an DNB
                response = self.search_page(query, start_record, page_size)
                
                # Parse Gesamtanzahl der Ergebnisse beim ersten Durchlauf
                if total_records is None:
                    try:
                        root = ET.fromstring(response)
                        num_elem = root.find('.//srw:numberOfRecords', dnb_ns)
                        if num_elem is not None and num_elem.text:
                            total_records = int(num_elem.text)
                            logger.info(f"DNB: Gesamtanzahl der Treffer: {total_records}")
                        else:
                            total_records = 0
                            logger.warning("DNB: Gesamtanzahl der Treffer konnte nicht ermittelt werden.")
                    except ET.ParseError as e:
                        logger.error(f"DNB: XML Parsing Fehler für Anzahl der Treffer: {e}")
                        total_records = 0
                
                # Verarbeite aktuelle Seite
                page_results = self.parse_results(response)
                all_results.extend(page_results)
                logger.info(f"DNB: Seite ab {start_record}: {len(page_results)} Treffer")
                
                # Prüfe, ob alle Ergebnisse abgerufen wurden
                if total_records is not None and start_record + page_size > total_records:
                    break
                
                # Nächste Seite
                start_record += page_size
                time.sleep(0.5)  # Pause zwischen Anfragen
                
            except Exception as e:
                logger.error(f"DNB: Fehler bei Anfrage ab Position {start_record}: {e}")
                break
                
        logger.info(f"DNB: Gesamtsuche abgeschlossen: {len(all_results)} Treffer")
        return all_results
        
    def search_page(self, query, start_record, page_size=1000):
        """Sendet eine einzelne Suchanfrage an die DNB"""
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": query,
            "recordSchema": "RDFxml",
            "maximumRecords": str(page_size),
            "startRecord": str(start_record)
        }
        
        response = requests.get(self.base_url, params=params)
        if response.status_code != 200:
            logger.error(f"DNB: HTTP-Fehler {response.status_code} für Anfrage ab Position {start_record}")
            response.raise_for_status()
            
        return response.text
        
    def parse_results(self, xml_text):
        """Parst die RDF/XML-Antwort der DNB"""
        results = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"DNB: XML Parsing Fehler: {e}")
            return results
            
        records = root.findall('.//srw:record', dnb_ns)
        if not records:
            logger.warning("DNB: Keine <record>-Elemente gefunden in der Antwort.")
            return results
            
        for record in records:
            try:
                record_data = record.find('srw:recordData', dnb_ns)
                if record_data is None:
                    continue
                    
                rdf_elem = record_data.find('rdf:RDF', dnb_ns)
                if rdf_elem is None:
                    continue
                    
                # Suche nach dem ersten rdf:Description mit einem dc:title
                desc = None
                for d in rdf_elem.findall('rdf:Description', dnb_ns):
                    if d.find('dc:title', dnb_ns) is not None:
                        desc = d
                        break
                        
                if desc is None:
                    continue
                    
                # Extrahiere Titel
                title_elem = desc.find('dc:title', dnb_ns)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Kein Titel"
                
                # Extrahiere Creator/Autor
                creator = ""
                creator_elem = desc.find('dc:creator', dnb_ns)
                if creator_elem is not None and creator_elem.text:
                    creator = creator_elem.text.strip()
                else:
                    creator_elem = desc.find('dcterms:creator', dnb_ns)
                    if creator_elem is not None and creator_elem.text:
                        creator = creator_elem.text.strip()
                    else:
                        creator_elem = desc.find('rdau:P60327', dnb_ns)
                        if creator_elem is not None and creator_elem.text:
                            creator = creator_elem.text.strip()
                        else:
                            creator = "Kein Creator"
                            
                # Extrahiere Erscheinungsjahr
                issued_elem = desc.find('dcterms:issued', dnb_ns)
                issued = issued_elem.text.strip() if issued_elem is not None and issued_elem.text else ""
                
                # Extrahiere Identifier und URL
                id_elem = desc.find('dc:identifier', dnb_ns)
                identifier = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                
                url_elem = desc.find('foaf:isPrimaryTopicOf', dnb_ns)
                url = url_elem.text.strip() if url_elem is not None and url_elem.text else ""
                
                # Extrahiere Verlag, wenn verfügbar
                publisher_elem = desc.find('dc:publisher', dnb_ns)
                publisher = publisher_elem.text.strip() if publisher_elem is not None and publisher_elem.text else ""
                
                # Extrahiere Sprache, wenn verfügbar
                language_elem = desc.find('dc:language', dnb_ns)
                language = language_elem.text.strip() if language_elem is not None and language_elem.text else ""
                
                # Erstelle Ergebnisdictionary
                result = {
                    "Titel": title,
                    "Creator": creator,
                    "Erscheinungsjahr": issued,
                    "Identifier": identifier,
                    "URL": url,
                    "Verlag": publisher,
                    "Sprache": language,
                    "Datenbank": "DNB"
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"DNB: Fehler beim Parsen eines einzelnen Datensatzes: {e}")
                
        return results

class PubMedConnector(DatabaseConnector):
    """Connector für die PubMed-Datenbank"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "PubMed"
        self.max_results_per_page = 1000
        self.search_fields = ["Alle Felder", "Titel/Abstract", "Autor", "Journal", "MeSH-Terms"]
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                       language=None, pub_type=None, field=None):
        """Baut eine PubMed-Anfrage"""
        query = base_query
        
        # Füge zusätzliche Suchbegriffe hinzu
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
            
        # Füge Datumsbereich hinzu, wenn vorhanden
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].replace("-", "/")
            end_date = date_range['end'].replace("-", "/")
            query += f" AND (\"{start_date}\"[Date - Publication] : \"{end_date}\"[Date - Publication])"
            
        # Füge Publikationstyp hinzu, wenn vorhanden
        if pub_type and pub_type != "Alle":
            query += f" AND {pub_type}[Publication Type]"
            
        # Füge Sprache hinzu, wenn vorhanden
        if language:
            query += f" AND {language}[Language]"
            
        return query
        
    def search(self, query, params=None):
        """Sucht in PubMed nach Publikationen"""
        logger.info(f"PubMed-Suche: {query}")
        
        # Default Parameter wenn nicht angegeben
        if params is None:
            params = {}
            
        name = params.get('name', 'PubMed-Suche')
        max_results = params.get('max_results', self.max_results_per_page)
        
        # Abruf der IDs über esearch
        esearch_url = self.base_url + "esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "usehistory": "y"
        }
        
        if self.api_key:
            esearch_params["api_key"] = self.api_key
            
        try:
            response = self.robust_get(esearch_url, esearch_params)
            esearch_xml = ET.fromstring(response.content)
            
            # Extrahiere WebEnv und QueryKey für effiziente Abfrage
            webenv = esearch_xml.find(".//WebEnv").text
            query_key = esearch_xml.find(".//QueryKey").text
            
            # Hole auch die ID-Liste für den Fall, dass wir WebEnv nicht nutzen können
            id_list = [node.text for node in esearch_xml.findall(".//Id")]
            
            count = len(id_list)
            logger.info(f"PubMed: {count} Treffer gefunden")
            
            if count == 0:
                return []
                
        except Exception as e:
            logger.error(f"PubMed: Fehler bei der ESearch-Anfrage: {e}")
            return []
            
        # Abruf der Details über efetch
        efetch_url = self.base_url + "efetch.fcgi"
        efetch_params = {
            "db": "pubmed",
            "WebEnv": webenv,
            "query_key": query_key,
            "retmode": "xml",
            "retmax": max_results
        }
        
        if self.api_key:
            efetch_params["api_key"] = self.api_key
            
        try:
            response = self.robust_get(efetch_url, efetch_params)
            efetch_xml = ET.fromstring(response.content)
            return self.parse_results(efetch_xml, name)
            
        except Exception as e:
            logger.error(f"PubMed: Fehler bei der EFetch-Anfrage: {e}")
            return []
            
    def parse_results(self, xml_content, name="PubMed-Suche"):
        """Parst die XML-Antwort von PubMed"""
        results = []
        
        for article in xml_content.findall(".//PubmedArticle"):
            try:
                # Extrahiere Titel
                title_el = article.find(".//ArticleTitle")
                title = title_el.text if title_el is not None else "Kein Titel"
                
                # Extrahiere Veröffentlichungsdatum
                pub_date_el = article.find(".//PubDate")
                year = pub_date_el.find("Year").text if pub_date_el is not None and pub_date_el.find("Year") is not None else "Kein Jahr"
                
                # Versuche, den Monat zu extrahieren
                month_el = pub_date_el.find("Month") if pub_date_el is not None else None
                month_raw = month_el.text if month_el is not None else ""
                
                # Versuche, den Monat als Zahl zu konvertieren
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
                
                # Extrahiere Autoren
                authors = []
                for author in article.findall(".//Author"):
                    ln = author.find(".//LastName")
                    fn = author.find(".//ForeName")
                    if ln is not None and fn is not None:
                        authors.append(f"{fn.text} {ln.text}")
                    else:
                        authors.append("Kein Name")
                authors_str = ", ".join(authors)
                
                # Extrahiere Publikationstypen
                pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
                pub_types_str = ", ".join(pub_types) if pub_types else "Keine Artikeltypen"
                
                # Extrahiere IDs
                pmid_el = article.find(".//PMID")
                pmid = pmid_el.text if pmid_el is not None else "Keine PMID"
                
                pmcid_el = article.find('.//ArticleId[@IdType="pmc"]')
                pmcid = pmcid_el.text if pmcid_el is not None else "Keine PMCID"
                
                doi_el = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_el.text if doi_el is not None else "Keine DOI"
                
                # Erstelle URLs
                doi_url = f"https://doi.org/{doi}" if doi != "Keine DOI" else "Keine DOI URL"
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "Keine PMID" else "Keine PubMed URL"
                
                # Extrahiere Affiliations
                affils = [aff.text for aff in article.findall(".//AffiliationInfo/Affiliation") if aff.text]
                affils_str = "\n".join(affils) if affils else "Keine Affiliationsdaten"
                
                # Extrahiere Journal-Informationen
                journal_el = article.find(".//Journal/Title")
                journal = journal_el.text if journal_el is not None else "Kein Journal"
                
                # Hole Zitationsanzahl
                citation_count = self.get_citation_count(pmid) if pmid != "Keine PMID" else "N/A"
                
                # Erstelle Ergebnisdictionary
                result = {
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
                    "Zitationsanzahl": citation_count,
                    "Journal": journal,
                    "Creator": authors[0] if authors else "Kein Creator",
                    "Erscheinungsjahr": year,
                    "Identifier": pmid,
                    "URL": pubmed_url,
                    "Datenbank": "PubMed"
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"PubMed: Fehler beim Parsen eines einzelnen Datensatzes: {e}")
                
        return results
        
    @lru_cache(maxsize=128)
    def get_citation_count(self, pmid):
        """Ruft die Anzahl der Zitierungen für eine PubMed-ID ab"""
        if not pmid or pmid == "Keine PMID":
            return "N/A"
            
        elink_url = self.base_url + "elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": pmid,
            "retmode": "xml"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
            
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
                    logger.warning(f"PubMed: 429 Error für PMID {pmid}. Warte {delay} Sekunden...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"PubMed: Fehler beim Abrufen der Zitationsanzahl für PMID {pmid}: {e}")
                    return "Fehler"
            except ET.ParseError as e:
                logger.error(f"PubMed: Parse-Fehler für PMID {pmid}: {e}")
                return "Fehler XML"
                
        logger.error(f"PubMed: Maximale Wiederholungen für PMID {pmid} überschritten.")
        return "Fehler 429"
        
    def robust_get(self, url, params, max_retries=3, initial_delay=0.5):
        """Führt eine robuste HTTP-Anfrage mit Wiederholungen und exponential Backoff durch"""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"PubMed: Fehler bei Anfrage an {url}: {e} (Versuch {attempt+1} von {max_retries})")
                time.sleep(delay)
                delay *= 2
                
        logger.error(f"PubMed: Alle Versuche für {url} fehlgeschlagen.")
        raise Exception("Maximale Anzahl an Wiederholungsversuchen überschritten")

####
# Factory für Datenbank-Connectoren
####
def get_database_connector(db_name):
    """Factory-Funktion zum Erstellen von Datenbank-Connector-Instanzen"""
    connectors = {
        "Deutsche Nationalbibliothek": DNBConnector,
        "PubMed": lambda api_key: PubMedConnector(api_key=settings.get("pubmed_api_key", ""))
    }
    
    if db_name in connectors:
        return connectors[db_name](None)
    else:
        logger.error(f"Unbekannte Datenbank: {db_name}")
        raise ValueError(f"Unbekannte Datenbank: {db_name}")

####
# GUI-Klasse für MedicalSpy
####
class MedicalSpyGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("MedicalSpy - Wissenschaftliches Publikations-Suchtool")
        self.master.geometry("1200x800")
        
        # Lade Einstellungen
        load_settings()
        
        # Initialisiere Variablen
        self.search_results = []
        self.output_path = settings.get("output_path", "./output")
        self.pause_flag = False
        self.stop_flag = False
        
        # Verfügbare Datenbanken
        self.available_databases = {
            "Deutsche Nationalbibliothek": "DNB",
            "PubMed": "PubMed"
        }
        
        # Aktiver Datenbank-Connector
        self.active_connector = None
        
        # Cache für Suchfeld-Optionen pro Datenbank
        self.search_field_options = {}
        
        # Erstelle GUI-Elemente
        self.create_widgets()
        
        # Setze anfängliche Datenbank
        initial_db = settings.get("default_database", "PubMed")
        if initial_db in self.available_databases:
            self.combobox_database.set(initial_db)
            self.on_database_change(None)
        
    def create_widgets(self):
        # Notebook mit Tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab: Datenbank
        self.tab_database = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_database, text="Datenbank")
        self.create_database_tab()
        
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
        
    ####
    # Tab "Datenbank" – Datenbankauswahl
    ####
    def create_database_tab(self):
        frame_db = ttk.LabelFrame(self.tab_database, text="Datenbank auswählen", padding=10)
        frame_db.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_db, text="Wählen Sie die zu durchsuchende Datenbank:").pack(anchor="w", pady=(0,10))
        
        self.combobox_database = ttk.Combobox(frame_db, values=list(self.available_databases.keys()), state="readonly", width=30)
        self.combobox_database.pack(fill=tk.X, padx=5, pady=5)
        self.combobox_database.bind("<<ComboboxSelected>>", self.on_database_change)
        
        # Informationen über die ausgewählte Datenbank
        self.database_info_frame = ttk.LabelFrame(self.tab_database, text="Datenbank-Informationen", padding=10)
        self.database_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.database_info_text = tk.Text(self.database_info_frame, wrap="word", height=15)
        self.database_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Datenbank-spezifische Einstellungen
        self.database_settings_frame = ttk.LabelFrame(self.tab_database, text="Datenbank-Einstellungen", padding=10)
        self.database_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.database_settings_frame, text="API-Key (falls erforderlich):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_db_api_key = ttk.Entry(self.database_settings_frame, width=40)
        self.entry_db_api_key.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_save_db_settings = ttk.Button(self.database_settings_frame, text="Einstellungen speichern", command=self.save_database_settings)
        self.btn_save_db_settings.grid(row=1, column=0, columnspan=2, pady=10)
        
    def on_database_change(self, event):
        """Wird aufgerufen, wenn die Datenbank geändert wird"""
        selected_db = self.combobox_database.get()
        if not selected_db:
            return
            
        # Hole Connector für die ausgewählte Datenbank
        try:
            self.active_connector = get_database_connector(selected_db)
            self.update_database_info()
            self.update_search_fields()
            
            # Aktualisiere API-Key aus Einstellungen
            if selected_db == "PubMed":
                self.entry_db_api_key.delete(0, tk.END)
                self.entry_db_api_key.insert(0, settings.get("pubmed_api_key", ""))
                
            log_message(self.text_log, f"Datenbank auf {selected_db} geändert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Datenbank: {e}")
            logger.error(f"Fehler beim Laden der Datenbank {selected_db}: {e}")
            
    def update_database_info(self):
        """Aktualisiert die Informationen über die ausgewählte Datenbank"""
        if self.active_connector:
            db_info = f"Name: {self.active_connector.name}\n"
            db_info += f"Max. Ergebnisse pro Seite: {self.active_connector.max_results_per_page}\n"
            db_info += f"Verfügbare Suchfelder: {', '.join(self.active_connector.search_fields)}\n"
            
            # Spezifische Informationen je nach Datenbank
            if isinstance(self.active_connector, PubMedConnector):
                db_info += "\nPubMed nutzt die E-Utilities API von NCBI. "
                db_info += "Sie bietet umfassenden Zugriff auf biomedizinische Literatur.\n"
                db_info += "Um API-Limits zu erhöhen, können Sie einen API-Key angeben."
            elif isinstance(self.active_connector, DNBConnector):
                db_info += "\nDie Deutsche Nationalbibliothek (DNB) bietet Zugriff auf alle deutschen und deutschsprachigen Publikationen.\n"
                db_info += "Die Suche erfolgt über die SRU-Schnittstelle mit CQL-Abfragen."
                
            self.database_info_text.config(state="normal")
            self.database_info_text.delete("1.0", tk.END)
            self.database_info_text.insert(tk.END, db_info)
            self.database_info_text.config(state="disabled")
            
    def update_search_fields(self):
        """Aktualisiert die Suchfelder-Optionen basierend auf der aktiven Datenbank"""
        if self.active_connector and hasattr(self, 'combobox_field'):
            self.combobox_field['values'] = self.active_connector.search_fields
            self.combobox_field.current(0)
            
    def save_database_settings(self):
        """Speichert datenbankspezifische Einstellungen"""
        selected_db = self.combobox_database.get()
        api_key = self.entry_db_api_key.get().strip()
        
        if selected_db == "PubMed":
            settings["pubmed_api_key"] = api_key
            # Aktualisiere aktiven Connector
            if self.active_connector:
                self.active_connector.api_key = api_key
                
        settings["default_database"] = selected_db
        save_settings()
        
        messagebox.showinfo("Einstellungen", "Datenbank-Einstellungen wurden gespeichert.")
        log_message(self.text_log, f"Datenbank-Einstellungen für {selected_db} gespeichert.")
            
    ####
    # Tab "Personen & Suche" – Personenverwaltung
    ####
    def create_person_tab(self):
        frame_input = ttk.LabelFrame(self.tab_person, text="Person hinzufügen/bearbeiten", padding=10)
        frame_input.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_input, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_name = ttk.Entry(frame_input, width=40)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Suchbegriff:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_person_query = ttk.Entry(frame_input, width=40)
        self.entry_person_query.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Suchfeld:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.combobox_field = ttk.Combobox(frame_input, values=["Alle Felder"], state="readonly", width=15)
        self.combobox_field.current(0)
        self.combobox_field.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Label(frame_input, text="Weitere Suchbegriffe:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_person_additional = ttk.Entry(frame_input, width=40)
        self.entry_person_additional.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame_input, text="DOI (optional):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
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
        columns = ("Name", "Suchbegriff", "Suchfeld", "Weitere Suchbegriffe")
        self.tree_persons = ttk.Treeview(frame_tree, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree_persons.heading(col, text=col)
            if col == "Name":
                self.tree_persons.column(col, width=200)
            elif col == "Suchbegriff":
                self.tree_persons.column(col, width=300)
            elif col == "Suchfeld":
                self.tree_persons.column(col, width=100)
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
        search_field = self.combobox_field.get()
        doi = self.entry_doi.get().strip()
        pub_type = self.combobox_pub_type.get()
        
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
            
        person = {
            "name": name,
            "search_term": query,
            "additional_search": additional,
            "search_field": search_field,
            "doi": doi,
            "pub_type": pub_type
        }
        
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
        
        self.combobox_field.set(person.get("search_field", "Alle Felder"))
        
        self.entry_doi.delete(0, tk.END)
        self.entry_doi.insert(0, person.get("doi", ""))
        
        self.combobox_pub_type.set(person.get("pub_type", "Alle"))
        
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
        search_field = self.combobox_field.get()
        doi = self.entry_doi.get().strip()
        pub_type = self.combobox_pub_type.get()
        
        if not name or not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte füllen Sie Name und Suchbegriff aus.")
            return
            
        persons[editing_person_index] = {
            "name": name,
            "search_term": query,
            "additional_search": additional,
            "search_field": search_field,
            "doi": doi,
            "pub_type": pub_type
        }
        
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
            values = (
                p["name"],
                p["search_term"],
                p.get("search_field", "Alle Felder"),
                p.get("additional_search", "")
            )
            self.tree_persons.insert("", tk.END, iid=str(i), values=values)
            
    def clear_person_inputs(self):
        self.entry_name.delete(0, tk.END)
        self.entry_person_query.delete(0, tk.END)
        self.entry_person_additional.delete(0, tk.END)
        self.entry_doi.delete(0, tk.END)
        self.combobox_field.set("Alle Felder")
        self.combobox_pub_type.set("Alle")
        
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
                
    ####
    # Tab "Erweiterte Optionen"
    ####
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
        self.combo_format = ttk.Combobox(frame_opts, values=["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"], state="readonly", width=15)
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
        
        # Erweiterte Suchoptionen für facettierte Suche
        frame_advanced = ttk.LabelFrame(self.tab_options, text="Erweiterte Suchoptionen", padding=10)
        frame_advanced.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_advanced, text="Max. Ergebnisse pro Person:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_max_results = ttk.Entry(frame_advanced, width=10)
        self.entry_max_results.insert(0, "1000")
        self.entry_max_results.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Checkbox für OR-Verknüpfung anstelle von AND
        self.var_or_search = tk.BooleanVar(value=False)
        chk_or = ttk.Checkbutton(frame_advanced, text="OR statt AND für zusätzliche Suchbegriffe verwenden", variable=self.var_or_search)
        chk_or.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Checkbox für exakte Phrasensuche
        self.var_exact_phrase = tk.BooleanVar(value=False)
        chk_exact = ttk.Checkbutton(frame_advanced, text="Exakte Phrasensuche für Suchbegriffe", variable=self.var_exact_phrase)
        chk_exact.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
    ####
    # Tab "Ausgabe" – Spaltenauswahl
    ####
    def create_output_tab(self):
        frame_output = ttk.LabelFrame(self.tab_output, text="Ausgabe-Einstellungen", padding=10)
        frame_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(frame_output, text="Wählen Sie die Ausgabespalten:").pack(anchor="w", pady=(0,5))
        
        frame_checkbuttons = ttk.Frame(frame_output)
        frame_checkbuttons.pack(fill=tk.BOTH, expand=True)
        
        # Kombinierte Liste aller möglichen Spalten aus beiden Datenbanken
        self.available_columns = [
            "Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL",
            "Autoren", "Veröffentlichungsjahr", "Veröffentlichungsmonat", "Publikationstypen",
            "Affiliations", "PubMed URL", "DOI URL", "PubMed-ID", "PMCID", "DOI",
            "Zitationsanzahl", "Journal", "Verlag", "Sprache", "Datenbank"
        ]
        
        self.output_vars = {}
        columns_per_row = 3
        
        for idx, col in enumerate(self.available_columns):
            var = tk.BooleanVar(value=col in settings.get("output_columns", []))
            self.output_vars[col] = var
            chk = ttk.Checkbutton(frame_checkbuttons, text=col, variable=var)
            chk.grid(row=idx // columns_per_row, column=idx % columns_per_row, sticky="w", padx=5, pady=2)
            
        # Frame für zusätzliche Ausgabeoptionen
        frame_options = ttk.Frame(frame_output)
        frame_options.pack(fill=tk.X, pady=10)
        
        # Option für eindeutige Dateinamen
        self.var_unique_filenames = tk.BooleanVar(value=settings.get("unique_filenames", False))
        chk_unique = ttk.Checkbutton(frame_options, text="Eindeutige Dateinamen mit Zeitstempel", variable=self.var_unique_filenames)
        chk_unique.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Option für Ausgabe der Zitationsanzahl (kann API-intensiv sein)
        self.var_include_citations = tk.BooleanVar(value=True)
        chk_citations = ttk.Checkbutton(frame_options, text="Zitationsanzahl einbeziehen (erhöht die API-Anfragen)", variable=self.var_include_citations)
        chk_citations.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Button zum Speichern der Ausgabeeinstellungen
        self.btn_save_output = ttk.Button(frame_output, text="Ausgabeeinstellungen speichern", command=self.save_output_settings)
        self.btn_save_output.pack(pady=10)
        
    def save_output_settings(self):
        """Speichert die Ausgabeeinstellungen"""
        selected_columns = [col for col, var in self.output_vars.items() if var.get()]
        settings["output_columns"] = selected_columns
        settings["unique_filenames"] = self.var_unique_filenames.get()
        
        save_settings()
        messagebox.showinfo("Einstellungen", "Ausgabeeinstellungen wurden gespeichert.")
        log_message(self.text_log, "Ausgabeeinstellungen gespeichert.")
        
    ####
    # Tab "Suchergebnisse"
    ####
    def create_results_tab(self):
        frame_results = ttk.LabelFrame(self.tab_results, text="Suchergebnisse", padding=10)
        frame_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Kombinierte Liste aller möglichen Spalten aus beiden Datenbanken für die Anzeige
        cols = [
            "Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier", "URL",
            "Autoren", "Veröffentlichungsjahr", "Veröffentlichungsmonat", "Publikationstypen",
            "Affiliations", "PubMed URL", "DOI URL", "PubMed-ID", "PMCID", "DOI",
            "Zitationsanzahl", "Journal", "Verlag", "Sprache", "Datenbank"
        ]
        
        self.tree_results = ttk.Treeview(frame_results, columns=cols, show="headings", selectmode="extended")
        for col in cols:
            self.tree_results.heading(col, text=col)
            self.tree_results.column(col, width=120, anchor="w")
            
        # Vertikaler Scrollbalken
        vsb = ttk.Scrollbar(frame_results, orient="vertical", command=self.tree_results.yview)
        self.tree_results.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Horizontaler Scrollbalken
        hsb = ttk.Scrollbar(frame_results, orient="horizontal", command=self.tree_results.xview)
        self.tree_results.configure(xscrollcommand=hsb.set)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        frame_result_buttons = ttk.Frame(self.tab_results)
        frame_result_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_export_results = ttk.Button(frame_result_buttons, text="Ergebnisse exportieren", command=self.export_results)
        self.btn_export_results.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear_results = ttk.Button(frame_result_buttons, text="Ergebnisse löschen", command=self.clear_results)
        self.btn_clear_results.pack(side=tk.LEFT, padx=5)
        
        self.btn_copy_selected = ttk.Button(frame_result_buttons, text="Ausgewählte kopieren", command=self.copy_selected_results)
        self.btn_copy_selected.pack(side=tk.LEFT, padx=5)
        
        # Suchfeld für das Filtern der Ergebnisse
        ttk.Label(frame_result_buttons, text="Filter:").pack(side=tk.LEFT, padx=(20,5))
        self.entry_result_filter = ttk.Entry(frame_result_buttons, width=30)
        self.entry_result_filter.pack(side=tk.LEFT, padx=5)
        self.entry_result_filter.bind("<KeyRelease>", self.filter_results)
        
        self.btn_filter = ttk.Button(frame_result_buttons, text="Filtern", command=lambda: self.filter_results(None))
        self.btn_filter.pack(side=tk.LEFT, padx=5)
        
    def filter_results(self, event):
        """Filtert die Ergebnisse basierend auf dem Eingabetext"""
        filter_text = self.entry_result_filter.get().lower()
        
        # Alle Elemente ausblenden
        for item in self.tree_results.get_children():
            self.tree_results.detach(item)
            
        # Gefilterte Elemente wieder anzeigen
        for i, result in enumerate(self.search_results):
            # Prüfe, ob der Filtertext in einem der Werte vorkommt
            found = False
            for value in result.values():
                if filter_text in str(value).lower():
                    found = True
                    break
                    
            if found or not filter_text:
                self.tree_results.reattach(str(i), "", i)
                
        log_message(self.text_log, f"Ergebnisse gefiltert nach: {filter_text}")
        
    def clear_results(self):
        """Löscht alle Suchergebnisse"""
        self.search_results = []
        self.update_results_tree()
        log_message(self.text_log, "Suchergebnisse gelöscht.")
        
    def copy_selected_results(self):
        """Kopiert die ausgewählten Ergebnisse in die Zwischenablage"""
        selected = self.tree_results.selection()
        if not selected:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie mindestens ein Ergebnis aus.")
            return
            
        # Extrahiere die ausgewählten Datensätze
        selected_data = []
        for item_id in selected:
            idx = int(item_id)
            selected_data.append(self.search_results[idx])
            
        # Konvertiere zu CSV-Format
        columns = [self.tree_results.heading(col)["text"] for col in self.tree_results["columns"]]
        
        csv_data = ",".join(columns) + "\n"
        for data in selected_data:
            row = []
            for col in columns:
                row.append(str(data.get(col, "")).replace(",", ";"))
            csv_data += ",".join(row) + "\n"
            
        # Kopiere in die Zwischenablage
        self.master.clipboard_clear()
        self.master.clipboard_append(csv_data)
        messagebox.showinfo("Kopiert", f"{len(selected)} Ergebnisse wurden in die Zwischenablage kopiert.")
        log_message(self.text_log, f"{len(selected)} Ergebnisse in die Zwischenablage kopiert.")
    
    ####
    # Tab "Gespeicherte Suchen"
    ####
    def create_saved_queries_tab(self):
        frame_saved = ttk.LabelFrame(self.tab_saved, text="Gespeicherte Suchanfragen", padding=10)
        frame_saved.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox mit Scrollbalken
        self.listbox_saved = tk.Listbox(frame_saved, height=10)
        vsb_saved = ttk.Scrollbar(frame_saved, orient="vertical", command=self.listbox_saved.yview)
        self.listbox_saved.configure(yscrollcommand=vsb_saved.set)
        self.listbox_saved.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        vsb_saved.pack(side=tk.LEFT, fill=tk.Y)
        
        # Frame für Beschreibung der ausgewählten Suche
        frame_query_details = ttk.LabelFrame(frame_saved, text="Details der Suchanfrage", padding=10)
        frame_query_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0))
        
        self.query_details_text = tk.Text(frame_query_details, wrap="word", height=10)
        self.query_details_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons für Speichern, Laden und Löschen
        frame_saved_buttons = ttk.Frame(self.tab_saved)
        frame_saved_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_save_query = ttk.Button(frame_saved_buttons, text="Aktuelle Suche speichern", command=self.save_current_query)
        self.btn_save_query.pack(side=tk.LEFT, padx=5)
        
        self.btn_load_query = ttk.Button(frame_saved_buttons, text="Ausgewählte laden", command=self.load_selected_query)
        self.btn_load_query.pack(side=tk.LEFT, padx=5)
        
        self.btn_delete_query = ttk.Button(frame_saved_buttons, text="Ausgewählte löschen", command=self.delete_selected_query)
        self.btn_delete_query.pack(side=tk.LEFT, padx=5)
        
        # Ereignis-Handler für Listenauswahl
        self.listbox_saved.bind("<<ListboxSelect>>", self.on_saved_query_select)
        
        self.refresh_saved_queries_listbox()
        
    def save_current_query(self):
        """Speichert die aktuelle Suchkonfiguration"""
        # Hole die aktuellen Suchparameter
        person = None
        if persons:
            # Verwende die erste Person als Basis für die Suchanfrage
            person = persons[0]
        else:
            # Erstelle temporäre Person aus den Eingabefeldern
            person = {
                "name": self.entry_name.get().strip(),
                "search_term": self.entry_person_query.get().strip(),
                "additional_search": self.entry_person_additional.get().strip(),
                "search_field": self.combobox_field.get(),
                "doi": self.entry_doi.get().strip(),
                "pub_type": self.combobox_pub_type.get()
            }
            
        if not person["search_term"]:
            messagebox.showwarning("Suchbegriff fehlt", "Bitte geben Sie mindestens einen Suchbegriff ein.")
            return
            
        # Hole weitere Parameter
        database = self.combobox_database.get()
        start_date = self.entry_start_date.get().strip()
        end_date = self.entry_end_date.get().strip()
        date_filter = self.var_date_filter.get()
        language = self.entry_language.get().strip()
        output_format = self.combo_format.get()
        
        # Erstelle Anzeigename
        display_name = f"{database}: {person['search_term']}"
        
        # Dialogfenster für Namen der Suchanfrage
        query_name = simpledialog.askstring("Suchanfrage speichern", "Name für die Suchanfrage:", initialvalue=display_name)
        if not query_name:
            return
            
        # Erstelle Suchanfragen-Objekt
        saved_query = {
            "display_name": query_name,
            "database": database,
            "person": person,
            "start_date": start_date,
            "end_date": end_date,
            "date_filter": date_filter,
            "language": language,
            "output_format": output_format,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Speichern
        current_queries = load_saved_queries()
        current_queries.append(saved_query)
        save_saved_queries(current_queries)
        
        self.refresh_saved_queries_listbox()
        log_message(self.text_log, f"Gespeicherte Suchanfrage '{query_name}' hinzugefügt.")
        
    def refresh_saved_queries_listbox(self):
        """Aktualisiert die Listbox mit gespeicherten Suchanfragen"""
        self.listbox_saved.delete(0, tk.END)
        queries = load_saved_queries()
        
        for q in queries:
            display = f"{q.get('display_name', '')}"
            self.listbox_saved.insert(tk.END, display)
            
    def on_saved_query_select(self, event):
        """Zeigt Details der ausgewählten Suchanfrage an"""
        selection = self.listbox_saved.curselection()
        if not selection:
            return
            
        index = selection[0]
        queries = load_saved_queries()
        
        if index < len(queries):
            q = queries[index]
            person = q.get("person", {})
            
            details = f"Name: {q.get('display_name', '')}\n"
            details += f"Datenbank: {q.get('database', '')}\n"
            details += f"Suchbegriff: {person.get('search_term', '')}\n"
            
            if person.get('additional_search'):
                details += f"Weitere Suchbegriffe: {person.get('additional_search', '')}\n"
                
            details += f"Suchfeld: {person.get('search_field', '')}\n"
            
            if q.get('start_date') and q.get('end_date'):
                details += f"Datumsbereich: {q.get('start_date', '')} bis {q.get('end_date', '')}\n"
                
            if q.get('language'):
                details += f"Sprache: {q.get('language', '')}\n"
                
            if q.get('timestamp'):
                details += f"Gespeichert am: {q.get('timestamp', '')}"
                
            self.query_details_text.config(state="normal")
            self.query_details_text.delete("1.0", tk.END)
            self.query_details_text.insert(tk.END, details)
            self.query_details_text.config(state="disabled")
            
    def load_selected_query(self):
        """Lädt die ausgewählte Suchanfrage in die Eingabefelder"""
        selection = self.listbox_saved.curselection()
        if not selection:
            messagebox.showwarning("Auswahl erforderlich", "Bitte wählen Sie eine gespeicherte Suchanfrage aus.")
            return
            
        index = selection[0]
        queries = load_saved_queries()
        
        if index < len(queries):
            q = queries[index]
            person = q.get("person", {})
            
            # Datenbank setzen
            database = q.get("database", "")
            if database in self.available_databases:
                self.combobox_database.set(database)
                self.on_database_change(None)
                
            # Person-Daten setzen
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, person.get("name", ""))
            
            self.entry_person_query.delete(0, tk.END)
            self.entry_person_query.insert(0, person.get("search_term", ""))
            
            self.entry_person_additional.delete(0, tk.END)
            self.entry_person_additional.insert(0, person.get("additional_search", ""))
            
            if person.get("search_field") in self.combobox_field["values"]:
                self.combobox_field.set(person.get("search_field"))
                
            self.entry_doi.delete(0, tk.END)
            self.entry_doi.insert(0, person.get("doi", ""))
            
            if person.get("pub_type") in self.combobox_pub_type["values"]:
                self.combobox_pub_type.set(person.get("pub_type"))
                
            # Weitere Parameter setzen
            if q.get("start_date"):
                self.entry_start_date.set_date(q.get("start_date"))
                
            if q.get("end_date"):
                self.entry_end_date.set_date(q.get("end_date"))
                
            self.var_date_filter.set(q.get("date_filter", True))
            
            self.entry_language.delete(0, tk.END)
            self.entry_language.insert(0, q.get("language", ""))
            
            if q.get("output_format") in self.combo_format["values"]:
                self.combo_format.set(q.get("output_format"))
                
            log_message(self.text_log, f"Gespeicherte Suchanfrage '{q.get('display_name', '')}' geladen.")
            
    def delete_selected_query(self):
        """Löscht die ausgewählte Suchanfrage"""
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
            
            # Lösche auch die Details-Anzeige
            self.query_details_text.config(state="normal")
            self.query_details_text.delete("1.0", tk.END)
            self.query_details_text.config(state="disabled")
            
            log_message(self.text_log, f"Gespeicherte Suchanfrage '{q.get('display_name', '')}' gelöscht.")
        
    ####
    # Tab "Log"
    ####
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
        
        self.btn_export_log_csv = ttk.Button(frame_log_buttons, text="Log als CSV exportieren", command=self.export_log_csv)
        self.btn_export_log_csv.pack(side=tk.LEFT, padx=5)
        
    def export_log_csv(self):
        """Exportiert das Log in eine CSV-Datei"""
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
        
    ####
    # Tab "Einstellungen"
    ####
    def create_settings_tab(self):
        frame_settings = ttk.LabelFrame(self.tab_settings, text="Allgemeine Einstellungen", padding=10)
        frame_settings.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_settings, text="Standard-Ausgabepfad:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_settings_output_path = ttk.Entry(frame_settings, width=40)
        self.entry_settings_output_path.grid(row=0, column=1, padx=5, pady=5)
        self.entry_settings_output_path.insert(0, settings.get("output_path", "./output"))
        
        self.btn_browse_output = ttk.Button(frame_settings, text="Durchsuchen", command=self.select_settings_output_path)
        self.btn_browse_output.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(frame_settings, text="Standard-Datenbank:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.combo_default_db = ttk.Combobox(frame_settings, values=list(self.available_databases.keys()), state="readonly", width=25)
        self.combo_default_db.grid(row=1, column=1, padx=5, pady=5)
        self.combo_default_db.set(settings.get("default_database", "PubMed"))
        
        # API Keys
        frame_api = ttk.LabelFrame(self.tab_settings, text="API-Einstellungen", padding=10)
        frame_api.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_api, text="PubMed API-Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_pubmed_api_key = ttk.Entry(frame_api, width=40)
        self.entry_pubmed_api_key.grid(row=0, column=1, padx=5, pady=5)
        self.entry_pubmed_api_key.insert(0, settings.get("pubmed_api_key", ""))
        
        # Einstellungen für die Benutzeroberfläche
        frame_ui = ttk.LabelFrame(self.tab_settings, text="Benutzeroberfläche", padding=10)
        frame_ui.pack(fill=tk.X, padx=10, pady=5)
        
        # Farbschema-Auswahl
        ttk.Label(frame_ui, text="Farbschema:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.combo_theme = ttk.Combobox(frame_ui, values=["Standard", "Hell", "Dunkel"], state="readonly", width=15)
        self.combo_theme.grid(row=0, column=1, padx=5, pady=5)
        self.combo_theme.set("Standard")
        
        # Schriftgrößen-Auswahl
        ttk.Label(frame_ui, text="Schriftgröße:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.combo_font_size = ttk.Combobox(frame_ui, values=["Klein", "Mittel", "Groß"], state="readonly", width=15)
        self.combo_font_size.grid(row=1, column=1, padx=5, pady=5)
        self.combo_font_size.set("Mittel")
        
        # Button zum Speichern aller Einstellungen
        self.btn_save_all_settings = ttk.Button(self.tab_settings, text="Alle Einstellungen speichern", command=self.save_all_settings)
        self.btn_save_all_settings.pack(pady=10)
        
    def select_settings_output_path(self):
        """Dialogfenster zum Auswählen des Standard-Ausgabepfads"""
        directory = filedialog.askdirectory()
        if directory:
            self.entry_settings_output_path.delete(0, tk.END)
            self.entry_settings_output_path.insert(0, directory)
            
    def save_all_settings(self):
        """Speichert alle Einstellungen"""
        # Allgemeine Einstellungen
        settings["output_path"] = self.entry_settings_output_path.get().strip()
        settings["default_database"] = self.combo_default_db.get()
        
        # API-Einstellungen
        settings["pubmed_api_key"] = self.entry_pubmed_api_key.get().strip()
        
        # Benutzeroberflächen-Einstellungen
        settings["ui_theme"] = self.combo_theme.get()
        settings["ui_font_size"] = self.combo_font_size.get()
        
        # Speichern
        save_settings()
        
        # Aktualisiere aktiven Connector, falls nötig
        if self.active_connector and isinstance(self.active_connector, PubMedConnector):
            self.active_connector.api_key = settings["pubmed_api_key"]
            
        messagebox.showinfo("Einstellungen", "Alle Einstellungen wurden erfolgreich gespeichert.")
        log_message(self.text_log, "Alle Einstellungen gespeichert.")
        
    ####
    # Tab "Analyse"
    ####
    def create_analysis_tab(self):
        frame_analysis = ttk.LabelFrame(self.tab_analysis, text="Analyse der Suchergebnisse", padding=10)
        frame_analysis.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.analysis_text = tk.Text(frame_analysis, wrap="word", state="disabled", height=10)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        # Container für Diagramme
        self.chart_frame = ttk.LabelFrame(self.tab_analysis, text="Visualisierung", padding=10)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        frame_analysis_buttons = ttk.Frame(self.tab_analysis)
        frame_analysis_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_run_analysis = ttk.Button(frame_analysis_buttons, text="Analyse aktualisieren", command=self.run_analysis)
        self.btn_run_analysis.pack(side=tk.LEFT, padx=5)
        
        # Dropdown für verschiedene Diagrammtypen
        ttk.Label(frame_analysis_buttons, text="Diagrammtyp:").pack(side=tk.LEFT, padx=(20,5))
        self.combo_chart_type = ttk.Combobox(frame_analysis_buttons, values=[
                "Publikationen pro Person", 
                "Publikationen pro Jahr", 
                "Publikationstypen",
                "Journalverteilung"
            ], state="readonly", width=20)
        self.combo_chart_type.current(0)
        self.combo_chart_type.pack(side=tk.LEFT, padx=5)
        
        self.btn_show_chart = ttk.Button(frame_analysis_buttons, text="Diagramm anzeigen", command=self.display_chart)
        self.btn_show_chart.pack(side=tk.LEFT, padx=5)
        
        self.btn_export_chart = ttk.Button(frame_analysis_buttons, text="Diagramm exportieren", command=self.export_chart)
        self.btn_export_chart.pack(side=tk.LEFT, padx=5)
        
    def run_analysis(self):
        """Führt eine grundlegende Analyse der Suchergebnisse durch"""
        if not self.search_results:
            messagebox.showinfo("Keine Daten", "Keine Suchergebnisse zur Analyse vorhanden.")
            return
            
        total = len(self.search_results)
        
        # Ergebnisse pro Person
        results_per_person = {}
        for result in self.search_results:
            person = result.get("Name", "Unbekannt")
            results_per_person[person] = results_per_person.get(person, 0) + 1
            
        # Ergebnisse pro Datenbank
        results_per_db = {}
        for result in self.search_results:
            db = result.get("Datenbank", "Unbekannt")
            results_per_db[db] = results_per_db.get(db, 0) + 1
            
        # Ergebnisse pro Jahr
        results_per_year = {}
        for result in self.search_results:
            year = result.get("Erscheinungsjahr", result.get("Veröffentlichungsjahr", "Unbekannt"))
            results_per_year[year] = results_per_year.get(year, 0) + 1
            
        # Erstelle Analysebericht
        report = f"Gesamtanzahl der Ergebnisse: {total}\n\n"
        
        report += "Ergebnisse pro Person:\n"
        for person, count in results_per_person.items():
            report += f"  - {person}: {count}\n"
            
        report += "\nErgebnisse pro Datenbank:\n"
        for db, count in results_per_db.items():
            report += f"  - {db}: {count}\n"
            
        report += "\nErgebnisse pro Jahr:\n"
        for year, count in sorted(results_per_year.items()):
            report += f"  - {year}: {count}\n"
            
        # Zeige den Bericht an
        self.analysis_text.config(state="normal")
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, report)
        self.analysis_text.config(state="disabled")
        
        log_message(self.text_log, "Analyse der Suchergebnisse aktualisiert.")
        
    def display_chart(self):
        """Erstellt und zeigt ein Diagramm basierend auf der ausgewählten Art an"""
        if not self.search_results:
            messagebox.showinfo("Keine Daten", "Keine Suchergebnisse für das Diagramm vorhanden.")
            return
            
        chart_type = self.combo_chart_type.get()
        
        if chart_type == "Publikationen pro Person":
            self.display_publications_per_person_chart()
        elif chart_type == "Publikationen pro Jahr":
            self.display_publications_per_year_chart()
        elif chart_type == "Publikationstypen":
            self.display_publication_type_chart()
        elif chart_type == "Journalverteilung":
            self.display_journal_distribution()
            
    def display_publications_per_person_chart(self):
        """Zeigt ein Balkendiagramm der Publikationen pro Person an"""
        results_per_person = {}
        for result in self.search_results:
            person = result.get("Name", "Unbekannt")
            results_per_person[person] = results_per_person.get(person, 0) + 1
            
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(results_per_person.keys(), results_per_person.values(), color="skyblue")
        ax.set_title("Anzahl der Publikationen pro Person")
        ax.set_xlabel("Person")
        ax.set_ylabel("Anzahl")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        self.display_figure(fig)
        log_message(self.text_log, "Diagramm 'Publikationen pro Person' aktualisiert.")
        
    def display_publications_per_year_chart(self):
        """Zeigt ein Liniendiagramm der Publikationen pro Jahr an"""
        results_per_year = {}
        for result in self.search_results:
            year = result.get("Erscheinungsjahr", result.get("Veröffentlichungsjahr", ""))
            if year and year.isdigit():
                results_per_year[int(year)] = results_per_year.get(int(year), 0) + 1
                
        if not results_per_year:
            messagebox.showinfo("Keine Daten", "Keine Jahresangaben in den Ergebnissen gefunden.")
            return
            
        # Sortiere nach Jahr
        years = sorted(results_per_year.keys())
        counts = [results_per_year[year] for year in years]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(years, counts, marker='o', linestyle='-', color="lightblue")
        ax.set_title("Publikationen pro Jahr")
        ax.set_xlabel("Jahr")
        ax.set_ylabel("Anzahl")
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Begrenze die Anzahl der x-Achsenbeschriftungen
        if len(years) > 10:
            step = len(years) // 10
            ax.set_xticks(years[::step])
            
        plt.tight_layout()
        
        self.display_figure(fig)
        log_message(self.text_log, "Diagramm 'Publikationen pro Jahr' aktualisiert.")
        
    def display_publication_type_chart(self):
        """Zeigt ein Kreisdiagramm der Publikationstypen an"""
        pub_type_counts = {}
        for result in self.search_results:
            types_str = result.get("Publikationstypen", "Keine Artikeltypen")
            types = [t.strip() for t in types_str.split(",") if t.strip()]
            if not types:
                types = ["Keine Artikeltypen"]
            for t in types:
                pub_type_counts[t] = pub_type_counts.get(t, 0) + 1
                
        if not pub_type_counts:
            messagebox.showinfo("Keine Daten", "Keine Publikationstypen in den Ergebnissen gefunden.")
            return
            
        # Limitiere auf die häufigsten Typen, wenn es zu viele gibt
        if len(pub_type_counts) > 8:
            sorted_types = sorted(pub_type_counts.items(), key=lambda x: x[1], reverse=True)
            top_types = dict(sorted_types[:7])
            other_count = sum(count for _, count in sorted_types[7:])
            if other_count > 0:
                top_types["Andere"] = other_count
            pub_type_counts = top_types
            
        fig, ax = plt.subplots(figsize=(8, 6))
        wedges, texts, autotexts = ax.pie(
            pub_type_counts.values(), 
            labels=pub_type_counts.keys(),
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        
        # Verbessere die Lesbarkeit der Labels
        for text in texts:
            text.set_fontsize(9)
            
        ax.set_title("Verteilung der Publikationstypen")
        ax.axis('equal')  # Sorgt für ein kreisförmiges Diagramm
        
        plt.tight_layout()
        
        self.display_figure(fig)
        log_message(self.text_log, "Diagramm 'Publikationstypen' aktualisiert.")
        
    def display_journal_distribution(self):
        """Zeigt ein Balkendiagramm der Journal-Verteilung an"""
        journal_counts = {}
        for result in self.search_results:
            journal = result.get("Journal", "")
            if journal:
                journal_counts[journal] = journal_counts.get(journal, 0) + 1
                
        if not journal_counts:
            messagebox.showinfo("Keine Daten", "Keine Journal-Informationen in den Ergebnissen gefunden.")
            return
            
        # Limitiere auf die häufigsten Journals
        if len(journal_counts) > 15:
            sorted_journals = sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)
            top_journals = dict(sorted_journals[:14])
            other_count = sum(count for _, count in sorted_journals[14:])
            if other_count > 0:
                top_journals["Andere"] = other_count
            journal_counts = top_journals
            
        fig, ax = plt.subplots(figsize=(10, 6))
        journals = list(journal_counts.keys())
        counts = list(journal_counts.values())
        
        # Horizontale Balken für bessere Lesbarkeit bei vielen Journals
        bars = ax.barh(journals, counts, color="lightblue")
        
        ax.set_title("Verteilung der Publikationen nach Journal")
        ax.set_xlabel("Anzahl der Publikationen")
        ax.set_ylabel("Journal")
        
        # Füge Werte am Ende der Balken hinzu
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f"{width:.0f}", 
                   ha='left', va='center')
                   
        plt.tight_layout()
        
        self.display_figure(fig)
        log_message(self.text_log, "Journal-Verteilung aktualisiert.")
        
    def display_figure(self, fig):
        """Zeigt eine Matplotlib-Figur im Diagramm-Frame an"""
        # Lösche vorherige Figur, falls vorhanden
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        # Erstelle Canvas für die Figur
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Speichere Referenz zur aktuellen Figur und Canvas
        self.current_figure = fig
        self.current_canvas = canvas
        
    def export_chart(self):
        """Exportiert das aktuelle Diagramm als Bilddatei"""
        if not hasattr(self, 'current_figure'):
            messagebox.showinfo("Kein Diagramm", "Es gibt kein Diagramm zum Exportieren.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG-Dateien", "*.png"),
                ("JPEG-Dateien", "*.jpg"),
                ("PDF-Dateien", "*.pdf"),
                ("SVG-Dateien", "*.svg"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export erfolgreich", f"Diagramm wurde als {file_path} exportiert.")
                log_message(self.text_log, f"Diagramm exportiert nach {file_path}")
            except Exception as e:
                messagebox.showerror("Export Fehler", f"Fehler beim Exportieren des Diagramms: {e}")
                log_message(self.text_log, f"Fehler beim Exportieren des Diagramms: {e}")
                
    ####
    # Steuerungsbuttons + Statusleiste
    ####
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
        
    ####
    # Suchvorgang starten (Threading)
    ####
    def start_search(self):
        """Startet die Suche in einem separaten Thread"""
        # Überprüfe, ob ein Datenbank-Connector aktiv ist
        if not self.active_connector:
            messagebox.showwarning("Keine Datenbank", "Bitte wählen Sie zuerst eine Datenbank aus.")
            return
            
        # Verwende, falls vorhanden, die Personenliste; ansonsten Einzel-Suche
        if persons:
            search_list = persons
        else:
            display_name = self.entry_name.get().strip()
            query_term = self.entry_person_query.get().strip()
            
            if not query_term:
                messagebox.showwarning("Kein Suchbegriff", "Bitte geben Sie einen Suchbegriff ein.")
                return
                
            person = {
                "name": display_name if display_name else query_term,
                "search_term": query_term,
                "additional_search": self.entry_person_additional.get().strip(),
                "search_field": self.combobox_field.get(),
                "doi": self.entry_doi.get().strip(),
                "pub_type": self.combobox_pub_type.get()
            }
            
            search_list = [person]
            
        if not search_list:
            messagebox.showwarning("Keine Personen", "Bitte fügen Sie mindestens eine Person hinzu oder geben Sie einen Suchbegriff ein.")
            return
            
        # Prüfe auf Ausgabepfad
        if not self.entry_output_path.get().strip():
            messagebox.showwarning("Ausgabepfad", "Bitte wählen Sie einen Ausgabepfad in den erweiterten Optionen.")
            return
            
        # Setze Flags zurück und initialisiere die Suche
        self.search_results = []
        self.update_results_tree()
        self.progress_var.set(0)
        self.pause_flag = False
        self.stop_flag = False
        
        # Aktiviere Steuerelemente
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")
        
        # Speichere den Startzeitpunkt für die Zeitschätzung
        self.search_start_time = time.time()
        
        # Starte Suche in separatem Thread
        t = threading.Thread(target=self.run_search, args=(search_list,))
        t.daemon = True
        t.start()
        
        log_message(self.text_log, "Suchvorgang gestartet.")
        
    def run_search(self, search_list):
        """Führt die Suche für alle Personen durch"""
        total = len(search_list)
        database_name = self.combobox_database.get()
        
        for idx, person in enumerate(search_list):
            if self.stop_flag:
                log_message(self.text_log, "Suche abgebrochen.")
                break
                
            while self.pause_flag:
                time.sleep(0.5)
                
            # Erstelle Query basierend auf Personendaten
            base_query = person["search_term"]
            additional = person.get("additional_search", "")
            
            # Übergebe Parameter an den Connector
            date_range = None
            if self.var_date_filter.get():
                date_range = {
                    'start': self.entry_start_date.get().strip(),
                    'end': self.entry_end_date.get().strip()
                }
                
            language = self.entry_language.get().strip() or None
            pub_type = person.get("pub_type") if person.get("pub_type") != "Alle" else None
            
            # Baue die Abfrage
            final_query = self.active_connector.construct_query(
                base_query, 
                additional, 
                date_range, 
                language, 
                pub_type
            )
            
            log_message(self.text_log, f"Suche für {person['name']} in {database_name} mit Query: {final_query}")
            
            # Durchführen der Suche
            try:
                max_results = int(self.entry_max_results.get().strip()) if self.entry_max_results.get().strip() else 1000
                results = self.active_connector.search(final_query, {'name': person['name'], 'max_results': max_results})
            except Exception as e:
                log_message(self.text_log, f"Fehler bei der Suche für {person['name']}: {e}")
                continue
                
            # Füge den Anzeige-Namen zu jedem Ergebnis hinzu (falls nicht bereits gesetzt)
            for res in results:
                if "Name" not in res:
                    res["Name"] = person["name"]
                    
            # Aktualisiere globale Ergebnisliste
            self.search_results.extend(results)
            
            # Aktualisiere Fortschritt und UI
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
            
            # Aktualisiere Statusleiste
            self.master.after(0, self.update_status, current_person, progress, results_count, remaining)
            
            log_message(self.text_log, f"Suche für {person['name']} abgeschlossen ({len(results)} Ergebnisse).")
            
            # Kurze Pause, um die API nicht zu überlasten
            time.sleep(0.5)
            
        # Suche beendet, UI zurücksetzen
        self.master.after(0, self.search_finished)
        
    def update_results_tree(self):
        """Aktualisiert den Treeview mit den aktuellen Suchergebnissen"""
        # Lösche alle Einträge
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
            
        # Füge alle Suchergebnisse hinzu
        for i, result in enumerate(self.search_results):
            # Hole die Werte für alle Spalten
            values = []
            for col in self.tree_results["columns"]:
                values.append(result.get(col, ""))
                
            self.tree_results.insert("", tk.END, iid=str(i), values=values)
            
    def pause_search(self):
        """Pausiert oder setzt die Suche fort"""
        self.pause_flag = not self.pause_flag
        if self.pause_flag:
            self.btn_pause.config(text="Weiter")
            log_message(self.text_log, "Suche pausiert.")
        else:
            self.btn_pause.config(text="Pause")
            log_message(self.text_log, "Suche fortgesetzt.")
            
    def stop_search(self):
        """Bricht die Suche ab"""
        self.stop_flag = True
        self.btn_stop.config(state="disabled")
        log_message(self.text_log, "Stop-Befehl empfangen. Suche wird abgebrochen.")
        
    def search_finished(self):
        """Wird aufgerufen, wenn die Suche beendet ist"""
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="Pause")
        self.btn_stop.config(state="disabled")
        self.progress_var.set(100)
        self.update_status("Fertig", 100, len(self.search_results), 0)
        log_message(self.text_log, "Alle Suchvorgänge abgeschlossen.")
        
    def update_status(self, current, progress, count, remaining):
        """Aktualisiert die Statusleiste"""
        status_text = f"Verarbeite: {current} | Fortschritt: {progress:.1f}% | Ergebnisse: {count} | Verbleibende Zeit: {remaining:.0f} s"
        self.status_label.config(text=status_text)
        
    def export_results(self):
        """Exportiert die Suchergebnisse in die angegebene Datei"""
        if not self.search_results:
            messagebox.showwarning("Keine Ergebnisse", "Es gibt keine Suchergebnisse zum Exportieren.")
            return
            
        out_
