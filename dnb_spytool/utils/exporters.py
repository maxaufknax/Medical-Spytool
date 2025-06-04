"""
Data export utilities for saving publication data in various formats.
"""

import json
import csv
import pandas as pd
from typing import List, Dict, Optional, Any
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import tempfile


class DataExporter:
    """Handles exporting publication data to various formats."""
    
    def __init__(self):
        """Initialize the data exporter."""
        self.supported_formats = ['csv', 'json', 'excel', 'xlsx']
    
    def export_publications(self, publications: List[Dict], format_type: str, 
                          output_path: str, include_metadata: bool = True) -> bool:
        """
        Export publication data to specified format.
        
        Args:
            publications: List of publication dictionaries
            format_type: Export format ('csv', 'json', 'excel', 'xlsx')
            output_path: Output file path
            include_metadata: Whether to include metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            if format_type.lower() == 'csv':
                return self._export_csv(publications, output_path, include_metadata)
            elif format_type.lower() == 'json':
                return self._export_json(publications, output_path, include_metadata)
            elif format_type.lower() in ['excel', 'xlsx']:
                return self._export_excel(publications, output_path, include_metadata)
            else:
                print(f"Unsupported format: {format_type}")
                return False
                
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def _export_csv(self, publications: List[Dict], output_path: str, 
                   include_metadata: bool = True) -> bool:
        """Export to CSV format."""
        try:
            # Validate output path
            if not output_path or not isinstance(output_path, str):
                raise ValueError(f"Invalid output path: {output_path}")
                
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise IOError(f"Cannot create directory {output_dir}: {str(e)}")
            
            # Define default fieldnames even for empty dataset
            default_fieldnames = ['id', 'title', 'authors', 'publication_year', 'publisher', 
                               'isbn', 'subjects', 'description', 'languages', 'type', 'primary_url', 
                               'doi', 'pmid', 'pmc', 'all_urls', 'database_source']
            
            # Flatten the data for CSV export
            flattened_data = []
            
            for pub in publications:
                # Handle different field name variations and ensure proper list conversion
                
                # Authors - handle string, list, or None
                authors_data = pub.get('authors') or pub.get('author', [])
                if authors_data is None:
                    authors_list = []
                elif isinstance(authors_data, str):
                    authors_list = [authors_data]
                elif isinstance(authors_data, list):
                    authors_list = authors_data
                else:
                    authors_list = [str(authors_data)]
                
                # Subjects - handle string, list, or None
                subjects_data = pub.get('subjects') or pub.get('subject', []) or pub.get('subject_headings', [])
                if subjects_data is None:
                    subjects_list = []
                elif isinstance(subjects_data, str):
                    subjects_list = [subjects_data]
                elif isinstance(subjects_data, list):
                    subjects_list = subjects_data
                else:
                    subjects_list = [str(subjects_data)]
                
                # ISBN - handle string, list, or None
                isbn_data = pub.get('isbn', [])
                if isbn_data is None:
                    isbn_list = []
                elif isinstance(isbn_data, str):
                    isbn_list = [isbn_data]
                elif isinstance(isbn_data, list):
                    isbn_list = isbn_data
                else:
                    isbn_list = [str(isbn_data)]
                
                # Language - handle string, list, or None
                language_data = pub.get('language', [])
                if language_data is None:
                    language_list = []
                elif isinstance(language_data, str):
                    language_list = [language_data]
                elif isinstance(language_data, list):
                    language_list = language_data
                else:
                    language_list = [str(language_data)]
                    
                # URLs - handle comprehensive URL data
                primary_url = pub.get('primary_url', '')
                doi = pub.get('doi', '')
                pmid = pub.get('pmid', '')
                pmc = pub.get('pmc', '')
                
                # Handle all_urls dictionary
                all_urls_data = pub.get('all_urls', {})
                if isinstance(all_urls_data, dict):
                    all_urls_str = '; '.join([f"{k}: {v}" for k, v in all_urls_data.items() if v])
                else:
                    all_urls_str = str(all_urls_data) if all_urls_data else ''
                
                # Legacy URL field for backward compatibility
                url_data = pub.get('url', [])
                if url_data is None:
                    url_list = []
                elif isinstance(url_data, str):
                    url_list = [url_data]
                elif isinstance(url_data, list):
                    url_list = url_data
                else:
                    url_list = [str(url_data)]
                
                flat_pub = {
                    'id': pub.get('id', ''),
                    'title': pub.get('title', ''),
                    'authors': '; '.join(authors_list),
                    'publication_year': pub.get('publication_year', ''),
                    'publisher': pub.get('publisher', ''),
                    'isbn': '; '.join(isbn_list),
                    'subjects': '; '.join(subjects_list),
                    'description': pub.get('description', ''),
                    'languages': '; '.join(language_list),
                    'type': pub.get('type', ''),
                    'primary_url': primary_url,
                    'doi': doi,
                    'pmid': pmid,
                    'pmc': pmc,
                    'all_urls': all_urls_str,
                    'database_source': pub.get('database_source', 'Unknown')
                }
                flattened_data.append(flat_pub)
            
            # Write to CSV - create file even if there's no data
            fieldnames = default_fieldnames
            if flattened_data:
                fieldnames = flattened_data[0].keys()
                
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                if include_metadata:
                    # Add metadata as comments
                    csvfile.write(f"# Export Date: {datetime.now().isoformat()}\n")
                    csvfile.write(f"# Total Records: {len(publications)}\n")
                    
                    # Count database sources
                    db_counts = {}
                    for pub in publications:
                        db_source = pub.get('database_source', 'Unknown')
                        db_counts[db_source] = db_counts.get(db_source, 0) + 1
                    
                    if len(db_counts) > 1:
                        csvfile.write(f"# Multi-Database Search: {', '.join([f'{db}: {count}' for db, count in db_counts.items()])}\n")
                    else:
                        data_source = list(db_counts.keys())[0] if db_counts else "Unknown"
                        csvfile.write(f"# Data Source: {data_source}\n")
                
                if flattened_data:
                    writer.writerows(flattened_data)
            
            print(f"Data exported to CSV: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def _export_json(self, publications: List[Dict], output_path: str, 
                    include_metadata: bool = True) -> bool:
        """Export to JSON format."""
        try:
            # Validate output path
            if not output_path or not isinstance(output_path, str):
                raise ValueError(f"Invalid output path: {output_path}")
                
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    raise IOError(f"Cannot create directory {output_dir}: {str(e)}")
                    
            export_data = {
                'publications': publications
            }
            
            if include_metadata:
                # Count database sources
                db_counts = {}
                for pub in publications:
                    db_source = pub.get('database_source', 'Unknown')
                    db_counts[db_source] = db_counts.get(db_source, 0) + 1
                
                export_data['metadata'] = {
                    'export_date': datetime.now().isoformat(),
                    'total_records': len(publications),
                    'database_sources': db_counts,
                    'format_version': '1.0'
                }
                
                if len(db_counts) > 1:
                    export_data['metadata']['search_type'] = 'multi_database'
                else:
                    export_data['metadata']['search_type'] = 'single_database'
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False, default=str)
            
            print(f"Data exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def _export_excel(self, publications: List[Dict], output_path: str, 
                     include_metadata: bool = True) -> bool:
        """Export to Excel format."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    print(f"Warning: Cannot create directory {output_dir}: {str(e)}")
                    # Continue anyway - we'll try to write to the current directory
            
            # Create a pandas DataFrame
            flattened_data = []
            
            for pub in publications:
                # Handle different field name variations and ensure proper list conversion
                
                # Authors - handle string, list, or None
                authors_data = pub.get('authors') or pub.get('author', [])
                if authors_data is None:
                    authors_list = []
                elif isinstance(authors_data, str):
                    authors_list = [authors_data]
                elif isinstance(authors_data, list):
                    authors_list = authors_data
                else:
                    authors_list = [str(authors_data)]
                
                # Subjects - handle string, list, or None
                subjects_data = pub.get('subjects') or pub.get('subject', []) or pub.get('subject_headings', [])
                if subjects_data is None:
                    subjects_list = []
                elif isinstance(subjects_data, str):
                    subjects_list = [subjects_data]
                elif isinstance(subjects_data, list):
                    subjects_list = subjects_data
                else:
                    subjects_list = [str(subjects_data)]
                
                # ISBN - handle string, list, or None
                isbn_data = pub.get('isbn', [])
                if isbn_data is None:
                    isbn_list = []
                elif isinstance(isbn_data, str):
                    isbn_list = [isbn_data]
                elif isinstance(isbn_data, list):
                    isbn_list = isbn_data
                else:
                    isbn_list = [str(isbn_data)]
                
                # Language - handle string, list, or None
                language_data = pub.get('language', [])
                if language_data is None:
                    language_list = []
                elif isinstance(language_data, str):
                    language_list = [language_data]
                elif isinstance(language_data, list):
                    language_list = language_data
                else:
                    language_list = [str(language_data)]
                    
                # URLs - handle comprehensive URL data
                primary_url = pub.get('primary_url', '')
                doi = pub.get('doi', '')
                pmid = pub.get('pmid', '')
                pmc = pub.get('pmc', '')
                
                # Handle all_urls dictionary
                all_urls_data = pub.get('all_urls', {})
                if isinstance(all_urls_data, dict):
                    all_urls_str = '; '.join([f"{k}: {v}" for k, v in all_urls_data.items() if v])
                else:
                    all_urls_str = str(all_urls_data) if all_urls_data else ''
                
                # Legacy URL field for backward compatibility
                url_data = pub.get('url', [])
                if url_data is None:
                    url_list = []
                elif isinstance(url_data, str):
                    url_list = [url_data]
                elif isinstance(url_data, list):
                    url_list = url_data
                else:
                    url_list = [str(url_data)]
                
                flat_pub = {
                    'ID': pub.get('id', ''),
                    'Title': pub.get('title', ''),
                    'Authors': '; '.join(authors_list),
                    'Publication Year': pub.get('publication_year', ''),
                    'Publisher': pub.get('publisher', ''),
                    'ISBN': '; '.join(isbn_list),
                    'Subjects': '; '.join(subjects_list),
                    'Description': pub.get('description', ''),
                    'Languages': '; '.join(language_list),
                    'Type': pub.get('type', ''),
                    'Primary URL': primary_url,
                    'DOI': doi,
                    'PMID': pmid,
                    'PMC': pmc,
                    'All URLs': all_urls_str,
                    'Database Source': pub.get('database_source', 'Unknown')
                }
                flattened_data.append(flat_pub)
            
            df = pd.DataFrame(flattened_data)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Publications', index=False)
                
                # Metadata sheet
                if include_metadata:
                    # Count database sources
                    db_counts = {}
                    for pub in publications:
                        db_source = pub.get('database_source', 'Unknown')
                        db_counts[db_source] = db_counts.get(db_source, 0) + 1
                    
                    metadata_rows = [
                        ['Export Date', datetime.now().isoformat()],
                        ['Total Records', len(publications)],
                        ['Format Version', '1.0']
                    ]
                    
                    # Add database source information
                    if len(db_counts) > 1:
                        metadata_rows.append(['Search Type', 'Multi-Database'])
                        for db, count in db_counts.items():
                            metadata_rows.append([f'{db} Records', count])
                    else:
                        metadata_rows.append(['Search Type', 'Single Database'])
                        db_source = list(db_counts.keys())[0] if db_counts else 'Unknown'
                        metadata_rows.append(['Data Source', db_source])
                    
                    metadata_df = pd.DataFrame(metadata_rows, columns=['Field', 'Value'])
                    
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"Data exported to Excel: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def export_analysis_report(self, analyzer, visualizer, output_path: str, 
                             format_type: str = 'pdf') -> bool:
        """
        Export comprehensive analysis report.
        
        Args:
            analyzer: PublicationAnalyzer instance
            visualizer: PublicationVisualizer instance
            output_path: Output file path
            format_type: Report format ('pdf', 'html')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if format_type.lower() == 'pdf':
                return self._export_pdf_report(analyzer, visualizer, output_path)
            elif format_type.lower() == 'html':
                return self._export_html_report(analyzer, visualizer, output_path)
            else:
                print(f"Unsupported report format: {format_type}")
                return False
                
        except Exception as e:
            print(f"Error exporting analysis report: {e}")
            return False
    
    def _export_pdf_report(self, analyzer, visualizer, output_path: str) -> bool:
        """Export analysis report as PDF."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph("DNB Publication Analysis Report", title_style))
            story.append(Spacer(1, 20))
            
            # Metadata
            metadata_style = ParagraphStyle(
                'Metadata',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", metadata_style))
            story.append(Paragraph("Data Source: German National Library (DNB)", metadata_style))
            story.append(Spacer(1, 30))
            
            # Summary statistics
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary_text = analyzer.generate_summary_report()
            
            # Convert summary to paragraphs
            for line in summary_text.split('\n'):
                if line.strip():
                    if line.startswith('==='):
                        continue  # Skip title line
                    elif line.strip().endswith(':'):
                        story.append(Paragraph(line, styles['Heading3']))
                    else:
                        story.append(Paragraph(line, styles['Normal']))
            
            story.append(PageBreak())
            
            # Detailed statistics
            story.append(Paragraph("Detailed Statistics", styles['Heading2']))
            
            stats = analyzer.get_basic_statistics()
            
            # Create statistics table
            stats_data = [
                ['Metric', 'Value'],
                ['Total Publications', f"{stats['total_publications']:,}"],
                ['Unique Authors', f"{stats['unique_authors']:,}"],
                ['Date Range', f"{stats['date_range']['earliest']} - {stats['date_range']['latest']}"],
                ['Publications with ISBN', f"{stats['publications_with_isbn']:,}"],
                ['Publications with URL', f"{stats['publications_with_url']:,}"],
                ['Average Title Length', f"{stats['average_title_length']:.1f} characters"],
                ['Collaboration Rate', f"{stats['collaboration_stats']['collaboration_rate']*100:.1f}%"]
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # Add charts if visualizer is available
            if visualizer:
                story.append(PageBreak())
                story.append(Paragraph("Visualizations", styles['Heading2']))
                
                # Create temporary directory for charts
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        # Generate and save charts
                        chart_files = visualizer.save_all_charts(temp_dir, "report")
                        
                        # Add note about charts
                        story.append(Paragraph(
                            "Note: For detailed visualizations, please refer to the separate chart files generated alongside this report.",
                            styles['Normal']
                        ))
                        
                    except Exception as e:
                        story.append(Paragraph(f"Error generating charts: {e}", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            print(f"PDF report exported: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error creating PDF report: {e}")
            return False
    
    def _export_html_report(self, analyzer, visualizer, output_path: str) -> bool:
        """Export analysis report as HTML."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
            
            stats = analyzer.get_basic_statistics()
            summary_text = analyzer.generate_summary_report()
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DNB Publication Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #007acc;
            border-bottom: 2px solid #eee;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #555;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
            font-style: italic;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007acc;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007acc;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            white-space: pre-line;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>DNB Publication Analysis Report</h1>
        
        <div class="metadata">
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Data Source: German National Library (DNB)
        </div>
        
        <h2>Key Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_publications']:,}</div>
                <div>Total Publications</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['unique_authors']:,}</div>
                <div>Unique Authors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['date_range']['span_years']}</div>
                <div>Years Covered</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['collaboration_stats']['collaboration_rate']*100:.1f}%</div>
                <div>Collaboration Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['publications_with_isbn']:,}</div>
                <div>Publications with ISBN</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['publications_with_url']:,}</div>
                <div>Publications with URL</div>
            </div>
        </div>
        
        <h2>Executive Summary</h2>
        <div class="summary">{summary_text}</div>
        
        <h2>Publication Types</h2>
        <ul>
"""
            
            for pub_type, count in list(stats['publication_types'].items())[:10]:
                html_content += f"            <li><strong>{pub_type}:</strong> {count:,} publications</li>\n"
            
            html_content += """        </ul>
        
        <h2>Top Publishers</h2>
        <ul>
"""
            
            for publisher, count in stats['top_publishers'][:10]:
                html_content += f"            <li><strong>{publisher}:</strong> {count:,} publications</li>\n"
            
            html_content += f"""        </ul>
        
        <div class="footer">
            Report generated by DNB Spytool v1.0.0<br>
            For more detailed analysis and visualizations, please use the full application.
        </div>
    </div>
</body>
</html>"""
            
            with open(output_path, 'w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            print(f"HTML report exported: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error creating HTML report: {e}")
            return False
    
    def get_export_summary(self, publications: List[Dict]) -> Dict:
        """
        Get summary information about the data to be exported.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            Summary information dictionary
        """
        if not publications:
            return {'total_records': 0, 'fields': [], 'size_estimate': '0 KB'}
        
        # Count fields
        all_fields = set()
        for pub in publications:
            all_fields.update(pub.keys())
        
        # Estimate size
        sample_json = json.dumps(publications[:min(10, len(publications))], default=str)
        estimated_size = len(sample_json) * len(publications) / min(10, len(publications))
        
        size_str = self._format_bytes(estimated_size)
        
        return {
            'total_records': len(publications),
            'fields': sorted(list(all_fields)),
            'size_estimate': size_str,
            'date_range': self._get_date_range(publications),
            'authors_count': self._count_unique_authors(publications)
        }
    
    def _format_bytes(self, bytes_size: float) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def _get_date_range(self, publications: List[Dict]) -> Dict:
        """Get date range from publications."""
        years = []
        for pub in publications:
            year = pub.get('publication_year')
            if year and isinstance(year, (int, str)):
                try:
                    years.append(int(year))
                except ValueError:
                    pass
        
        if years:
            return {'earliest': min(years), 'latest': max(years)}
        return {'earliest': None, 'latest': None}
    
    def _count_unique_authors(self, publications: List[Dict]) -> int:
        """Count unique authors in publications."""
        authors = set()
        for pub in publications:
            pub_authors = pub.get('author', [])
            if isinstance(pub_authors, list):
                authors.update(pub_authors)
            elif isinstance(pub_authors, str):
                authors.add(pub_authors)
        
        return len(authors)
    
    def export_to_csv(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to CSV format."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError(f"Invalid file path: {file_path}")
            
        # Check if directory exists or can be created
        dir_path = os.path.dirname(file_path)
        if dir_path:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except (OSError, PermissionError) as e:
                print(f"Warning: Cannot create directory for path {file_path}: {str(e)}")
                # Continue anyway - we'll try to write to the current directory
                
        return self._export_csv(publications, file_path, True)
    
    def export_to_json(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to JSON format."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError(f"Invalid file path: {file_path}")
            
        # Check if directory exists or can be created
        dir_path = os.path.dirname(file_path)
        if dir_path:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except (OSError, PermissionError) as e:
                print(f"Warning: Cannot create directory for path {file_path}: {str(e)}")
                # Continue anyway - we'll try to write to the current directory
                
        return self._export_json(publications, file_path, True)
    
    def export_to_excel(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to Excel format."""
        if not file_path or not isinstance(file_path, str):
            raise ValueError(f"Invalid file path: {file_path}")
            
        # Check if directory exists or can be created
        dir_path = os.path.dirname(file_path)
        if dir_path:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except (OSError, PermissionError) as e:
                print(f"Warning: Cannot create directory for path {file_path}: {str(e)}")
                # Continue anyway - we'll try to write to the current directory
                
        return self._export_excel(publications, file_path, True)
    
    def export_to_xlsx(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to Excel format (alias for export_to_excel)."""
        return self._export_excel(publications, file_path, True)
    
    def export_to_pdf(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to PDF format."""
        try:
            from dnb_spytool.analytics.analyzer import PublicationAnalyzer
            analyzer = PublicationAnalyzer(publications)
            return self._export_pdf_report(analyzer, None, file_path)
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            return False
    
    def export_to_html(self, publications: List[Dict], file_path: str) -> bool:
        """Export publications to HTML format."""
        try:
            from dnb_spytool.analytics.analyzer import PublicationAnalyzer
            analyzer = PublicationAnalyzer(publications)
            return self._export_html_report(analyzer, None, file_path)
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return False
