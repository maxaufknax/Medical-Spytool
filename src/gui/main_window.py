import sys
import os
import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTableWidget, QTableWidgetItem, QProgressBar, 
                           QStatusBar, QTextEdit, QTabWidget, QCheckBox,
                           QSpinBox, QComboBox, QGroupBox, QMessageBox,
                           QFileDialog, QSplitter, QHeaderView, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# Import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.dnb_client import DNBClient
from api.pubmed_client import PubMedClient
from core.exporters import CSVExporter, JSONExporter, ExcelExporter, ReportExporter
from core.visualizer import PublicationVisualizer

logger = logging.getLogger(__name__)

class SearchWorker(QThread):
    """Worker thread for performing publication searches."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, author_name: str, search_dnb: bool, search_pubmed: bool, 
                 max_results: Optional[int] = None):
        super().__init__()
        self.author_name = author_name
        self.search_dnb = search_dnb
        self.search_pubmed = search_pubmed
        self.max_results = max_results
        self.dnb_client = DNBClient()
        self.pubmed_client = PubMedClient()
        
    def run(self):
        """Execute the search in a separate thread."""
        try:
            all_publications = []
            total_sources = sum([self.search_dnb, self.search_pubmed])
            current_source = 0
            
            # DNB Search
            if self.search_dnb:
                self.status_updated.emit("Searching DNB database...")
                self.progress_updated.emit(int((current_source / total_sources) * 50))
                
                try:
                    dnb_results = self.dnb_client.search_publications(
                        self.author_name, self.max_results
                    )
                    all_publications.extend(dnb_results)
                    self.status_updated.emit(f"DNB: Found {len(dnb_results)} publications")
                except Exception as e:
                    logger.error(f"DNB search failed: {e}")
                    self.status_updated.emit(f"DNB search failed: {str(e)}")
                
                current_source += 1
                self.progress_updated.emit(int((current_source / total_sources) * 50))
            
            # PubMed Search
            if self.search_pubmed:
                self.status_updated.emit("Searching PubMed database...")
                self.progress_updated.emit(50 + int((current_source / total_sources) * 50))
                
                try:
                    pubmed_results = self.pubmed_client.search_publications(
                        self.author_name, self.max_results
                    )
                    all_publications.extend(pubmed_results)
                    self.status_updated.emit(f"PubMed: Found {len(pubmed_results)} publications")
                except Exception as e:
                    logger.error(f"PubMed search failed: {e}")
                    self.status_updated.emit(f"PubMed search failed: {str(e)}")
            
            self.progress_updated.emit(100)
            self.status_updated.emit(f"Search completed: {len(all_publications)} total publications found")
            self.results_ready.emit(all_publications)
            
        except Exception as e:
            logger.error(f"Search worker error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

class ExportWorker(QThread):
    """Worker thread for exporting data."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, publications: List[Dict[str, Any]], export_format: str, 
                 filename: str, include_report: bool = False):
        super().__init__()
        self.publications = publications
        self.export_format = export_format
        self.filename = filename
        self.include_report = include_report
        
    def run(self):
        """Execute the export in a separate thread."""
        try:
            self.progress_updated.emit(10)
            self.status_updated.emit(f"Preparing {self.export_format} export...")
            
            # Select appropriate exporter
            if self.export_format.lower() == 'csv':
                exporter = CSVExporter()
            elif self.export_format.lower() == 'json':
                exporter = JSONExporter()
            elif self.export_format.lower() == 'excel':
                exporter = ExcelExporter()
            else:
                raise ValueError(f"Unsupported export format: {self.export_format}")
            
            self.progress_updated.emit(30)
            self.status_updated.emit("Exporting data...")
            
            # Export publications
            exporter.export(self.publications, self.filename)
            
            self.progress_updated.emit(70)
            
            # Generate report if requested
            if self.include_report:
                self.status_updated.emit("Generating analysis report...")
                report_exporter = ReportExporter()
                report_filename = self.filename.rsplit('.', 1)[0] + '_report.pdf'
                report_exporter.export_report(self.publications, report_filename)
                self.progress_updated.emit(90)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Export completed successfully")
            self.export_completed.emit(self.filename)
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

class DNBSpytoolMainWindow(QMainWindow):
    """Main application window for DNB Spytool."""
    
    def __init__(self):
        super().__init__()
        self.publications = []
        self.search_worker = None
        self.export_worker = None
        
        self.init_ui()
        self.setup_logging()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("DNB Spytool - Medical Publication Research Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon if available
        try:
            self.setWindowIcon(QIcon('assets/icon.ico'))
        except:
            pass
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_search_tab()
        self.create_results_tab()
        self.create_analytics_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.connection_label = QLabel("Connection: Not tested")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Test connections on startup
        QTimer.singleShot(1000, self.test_connections)
        
    def create_search_tab(self):
        """Create the search tab."""
        search_widget = QWidget()
        layout = QVBoxLayout(search_widget)
        
        # Search input group
        search_group = QGroupBox("Search Parameters")
        search_layout = QVBoxLayout(search_group)
        
        # Author name input
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("Author Name:"))
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Enter author name (e.g., 'John Smith')")
        self.author_input.returnPressed.connect(self.start_search)
        author_layout.addWidget(self.author_input)
        search_layout.addLayout(author_layout)
        
        # Database selection
        db_layout = QHBoxLayout()
        self.dnb_checkbox = QCheckBox("Search DNB")
        self.dnb_checkbox.setChecked(True)
        self.pubmed_checkbox = QCheckBox("Search PubMed")
        self.pubmed_checkbox.setChecked(True)
        db_layout.addWidget(self.dnb_checkbox)
        db_layout.addWidget(self.pubmed_checkbox)
        db_layout.addStretch()
        search_layout.addLayout(db_layout)
        
        # Max results
        max_results_layout = QHBoxLayout()
        max_results_layout.addWidget(QLabel("Max Results:"))
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setMinimum(1)
        self.max_results_spin.setMaximum(10000)
        self.max_results_spin.setValue(1000)
        self.max_results_spin.setSpecialValueText("Unlimited")
        max_results_layout.addWidget(self.max_results_spin)
        max_results_layout.addStretch()
        search_layout.addLayout(max_results_layout)
        
        # Search button
        self.search_button = QPushButton("Start Search")
        self.search_button.clicked.connect(self.start_search)
        self.search_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        search_layout.addWidget(self.search_button)
        
        layout.addWidget(search_group)
        
        # Search log
        log_group = QGroupBox("Search Log")
        log_layout = QVBoxLayout(log_group)
        self.search_log = QTextEdit()
        self.search_log.setReadOnly(True)
        self.search_log.setMaximumHeight(200)
        log_layout.addWidget(self.search_log)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.tab_widget.addTab(search_widget, "Search")
        
    def create_results_tab(self):
        """Create the results tab."""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        
        # Results summary
        summary_layout = QHBoxLayout()
        self.results_label = QLabel("No results loaded")
        summary_layout.addWidget(self.results_label)
        summary_layout.addStretch()
        
        # Export controls
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Export as:"))
        
        self.export_csv_btn = QPushButton("CSV")
        self.export_csv_btn.clicked.connect(lambda: self.export_data('csv'))
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("JSON")
        self.export_json_btn.clicked.connect(lambda: self.export_data('json'))
        export_layout.addWidget(self.export_json_btn)
        
        self.export_excel_btn = QPushButton("Excel")
        self.export_excel_btn.clicked.connect(lambda: self.export_data('excel'))
        export_layout.addWidget(self.export_excel_btn)
        
        self.include_report_checkbox = QCheckBox("Include Analysis Report")
        export_layout.addWidget(self.include_report_checkbox)
        
        export_layout.addStretch()
        summary_layout.addLayout(export_layout)
        layout.addLayout(summary_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.setup_results_table()
        layout.addWidget(self.results_table)
        
        self.tab_widget.addTab(results_widget, "Results")
        
    def create_analytics_tab(self):
        """Create the analytics tab."""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Analytics controls
        controls_layout = QHBoxLayout()
        self.generate_charts_btn = QPushButton("Generate Charts")
        self.generate_charts_btn.clicked.connect(self.generate_analytics)
        controls_layout.addWidget(self.generate_charts_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Charts area
        self.analytics_area = QTextEdit()
        self.analytics_area.setReadOnly(True)
        self.analytics_area.setText("Load search results and click 'Generate Charts' to view analytics.")
        layout.addWidget(self.analytics_area)
        
        self.tab_widget.addTab(analytics_widget, "Analytics")
        
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Connection settings
        connection_group = QGroupBox("Connection Settings")
        connection_layout = QVBoxLayout(connection_group)
        
        test_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("Test Connections")
        self.test_connection_btn.clicked.connect(self.test_connections)
        test_layout.addWidget(self.test_connection_btn)
        test_layout.addStretch()
        connection_layout.addLayout(test_layout)
        
        layout.addWidget(connection_group)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QVBoxLayout(logging_group)
        
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self.change_log_level)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        logging_layout.addLayout(log_level_layout)
        
        layout.addWidget(logging_group)
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def setup_results_table(self):
        """Setup the results table."""
        headers = ["Source", "Title", "Authors", "Year", "Journal", "DOI", "Publisher"]
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
    def setup_logging(self):
        """Setup logging configuration."""
        # Create a custom handler to display logs in the GUI
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)
                
        # Add GUI log handler
        gui_handler = GuiLogHandler(self.search_log)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(gui_handler)
        logger.setLevel(logging.INFO)
        
    def start_search(self):
        """Start the publication search."""
        author_name = self.author_input.text().strip()
        
        if not author_name:
            QMessageBox.warning(self, "Warning", "Please enter an author name.")
            return
            
        if not (self.dnb_checkbox.isChecked() or self.pubmed_checkbox.isChecked()):
            QMessageBox.warning(self, "Warning", "Please select at least one database to search.")
            return
            
        # Disable search controls
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        self.publications = []
        self.update_results_display()
        
        # Start search worker
        max_results = self.max_results_spin.value() if self.max_results_spin.value() > 1 else None
        
        self.search_worker = SearchWorker(
            author_name,
            self.dnb_checkbox.isChecked(),
            self.pubmed_checkbox.isChecked(),
            max_results
        )
        
        # Connect signals
        self.search_worker.progress_updated.connect(self.progress_bar.setValue)
        self.search_worker.status_updated.connect(self.status_bar.showMessage)
        self.search_worker.results_ready.connect(self.handle_search_results)
        self.search_worker.error_occurred.connect(self.handle_search_error)
        self.search_worker.finished.connect(self.search_finished)
        
        self.search_worker.start()
        
    def handle_search_results(self, publications: List[Dict[str, Any]]):
        """Handle search results."""
        self.publications = publications
        self.update_results_display()
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(1)
        
    def handle_search_error(self, error_message: str):
        """Handle search errors."""
        QMessageBox.critical(self, "Search Error", f"Search failed: {error_message}")
        
    def search_finished(self):
        """Handle search completion."""
        self.search_button.setEnabled(True)
        self.search_button.setText("Start Search")
        self.progress_bar.setVisible(False)
        self.search_worker = None
        
    def update_results_display(self):
        """Update the results table."""
        self.results_table.setRowCount(len(self.publications))
        
        for row, pub in enumerate(self.publications):
            items = [
                pub.get('source', ''),
                pub.get('title', '')[:100] + '...' if len(pub.get('title', '')) > 100 else pub.get('title', ''),
                ', '.join(pub.get('authors', []))[:50] + '...' if len(', '.join(pub.get('authors', []))) > 50 else ', '.join(pub.get('authors', [])),
                str(pub.get('year', '')),
                pub.get('journal', ''),
                pub.get('doi', ''),
                pub.get('publisher', '')
            ]
            
            for col, item in enumerate(items):
                self.results_table.setItem(row, col, QTableWidgetItem(str(item)))
        
        # Update summary
        dnb_count = sum(1 for pub in self.publications if pub.get('source') == 'DNB')
        pubmed_count = sum(1 for pub in self.publications if pub.get('source') == 'PubMed')
        
        summary_text = f"Total: {len(self.publications)} publications "
        if dnb_count > 0:
            summary_text += f"(DNB: {dnb_count}"
        if pubmed_count > 0:
            summary_text += f", PubMed: {pubmed_count}" if dnb_count > 0 else f"(PubMed: {pubmed_count}"
        if dnb_count > 0 or pubmed_count > 0:
            summary_text += ")"
            
        self.results_label.setText(summary_text)
        
        # Enable/disable export buttons
        has_results = len(self.publications) > 0
        self.export_csv_btn.setEnabled(has_results)
        self.export_json_btn.setEnabled(has_results)
        self.export_excel_btn.setEnabled(has_results)
        self.generate_charts_btn.setEnabled(has_results)
        
    def export_data(self, format_type: str):
        """Export data in the specified format."""
        if not self.publications:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
            
        # Get filename from user
        extensions = {
            'csv': 'CSV Files (*.csv)',
            'json': 'JSON Files (*.json)',
            'excel': 'Excel Files (*.xlsx)'
        }
        
        filename, _ = QFileDialog.getSaveFileName(
            self, f"Export as {format_type.upper()}", 
            f"publications.{format_type.lower()}", 
            extensions[format_type]
        )
        
        if not filename:
            return
            
        # Start export worker
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.export_worker = ExportWorker(
            self.publications, 
            format_type, 
            filename,
            self.include_report_checkbox.isChecked()
        )
        
        # Connect signals
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        self.export_worker.status_updated.connect(self.status_bar.showMessage)
        self.export_worker.export_completed.connect(self.handle_export_completed)
        self.export_worker.error_occurred.connect(self.handle_export_error)
        self.export_worker.finished.connect(self.export_finished)
        
        self.export_worker.start()
        
    def handle_export_completed(self, filename: str):
        """Handle successful export."""
        QMessageBox.information(self, "Export Successful", f"Data exported to:\n{filename}")
        
    def handle_export_error(self, error_message: str):
        """Handle export errors."""
        QMessageBox.critical(self, "Export Error", f"Export failed: {error_message}")
        
    def export_finished(self):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        self.export_worker = None
        
    def generate_analytics(self):
        """Generate analytics charts."""
        if not self.publications:
            QMessageBox.warning(self, "Warning", "No data available for analytics.")
            return
            
        try:
            visualizer = PublicationVisualizer()
            
            # Generate charts and save to temp files
            charts_info = []
            
            # Publications by year
            year_chart = visualizer.plot_publications_by_year(self.publications)
            if year_chart:
                charts_info.append("✓ Publications by year chart generated")
            
            # Publications by source
            source_chart = visualizer.plot_publications_by_source(self.publications)
            if source_chart:
                charts_info.append("✓ Publications by source chart generated")
            
            # Keywords analysis
            keywords_chart = visualizer.plot_top_keywords(self.publications)
            if keywords_chart:
                charts_info.append("✓ Top keywords chart generated")
            
            # Update analytics display
            info_text = "Analytics Generated:\n\n" + "\n".join(charts_info)
            info_text += "\n\nNote: Charts are displayed in separate windows and can be saved manually."
            
            self.analytics_area.setText(info_text)
            
            # Switch to analytics tab
            self.tab_widget.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Analytics Error", f"Failed to generate analytics: {str(e)}")
            
    def test_connections(self):
        """Test connections to DNB and PubMed APIs."""
        self.connection_label.setText("Testing connections...")
        
        try:
            dnb_client = DNBClient()
            pubmed_client = PubMedClient()
            
            dnb_status = dnb_client.test_connection()
            pubmed_status = pubmed_client.test_connection()
            
            status_text = "Connection: "
            if dnb_status and pubmed_status:
                status_text += "✓ All services online"
                self.connection_label.setStyleSheet("color: green")
            elif dnb_status or pubmed_status:
                status_text += "⚠ Partial connectivity"
                self.connection_label.setStyleSheet("color: orange")
            else:
                status_text += "✗ No connectivity"
                self.connection_label.setStyleSheet("color: red")
                
            self.connection_label.setText(status_text)
            
        except Exception as e:
            self.connection_label.setText("Connection: Error")
            self.connection_label.setStyleSheet("color: red")
            logger.error(f"Connection test failed: {e}")
            
    def change_log_level(self, level: str):
        """Change the logging level."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        logger.setLevel(level_map[level])
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Clean up worker threads
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()
            
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.quit()
            self.export_worker.wait()
            
        event.accept()

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("DNB Spytool")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = DNBSpytoolMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
