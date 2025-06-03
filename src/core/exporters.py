import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseExporter:
    """Base class for all exporters."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def prepare_data(self, publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare publication data for export, ensuring source column is included."""
        prepared_data = []
        
        for pub in publications:
            # Ensure all required fields are present
            prepared_pub = {
                'source': pub.get('source', 'Unknown'),
                'title': pub.get('title', ''),
                'authors': '; '.join(pub.get('authors', [])) if isinstance(pub.get('authors'), list) else str(pub.get('authors', '')),
                'year': pub.get('year', ''),
                'journal': pub.get('journal', ''),
                'doi': pub.get('doi', ''),
                'abstract': pub.get('abstract', ''),
                'keywords': '; '.join(pub.get('keywords', [])) if isinstance(pub.get('keywords'), list) else str(pub.get('keywords', '')),
                'language': pub.get('language', ''),
                'publisher': pub.get('publisher', ''),
                'isbn': pub.get('isbn', ''),
                'issn': pub.get('issn', '')
            }
            prepared_data.append(prepared_pub)
        
        return prepared_data

class CSVExporter(BaseExporter):
    """Export publications to CSV format."""
    
    def export(self, publications: List[Dict[str, Any]], filename: str) -> None:
        """Export publications to CSV file."""
        prepared_data = self.prepare_data(publications)
        
        if not prepared_data:
            raise ValueError("No publications to export")
        
        df = pd.DataFrame(prepared_data)
        
        # Reorder columns to put source first
        column_order = ['source', 'title', 'authors', 'year', 'journal', 'doi', 
                       'abstract', 'keywords', 'language', 'publisher', 'isbn', 'issn']
        df = df.reindex(columns=column_order)
        
        # Add metadata header
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            f.write(f"# DNB Spytool Export\n")
            f.write(f"# Generated: {self.timestamp}\n")
            f.write(f"# Total Publications: {len(publications)}\n")
            f.write(f"# Sources: {', '.join(set(pub['source'] for pub in prepared_data))}\n")
            f.write("#\n")
        
        # Append CSV data
        df.to_csv(filename, mode='a', index=False, encoding='utf-8')
        logger.info(f"Exported {len(publications)} publications to CSV: {filename}")

class JSONExporter(BaseExporter):
    """Export publications to JSON format."""
    
    def export(self, publications: List[Dict[str, Any]], filename: str) -> None:
        """Export publications to JSON file."""
        prepared_data = self.prepare_data(publications)
        
        export_data = {
            'metadata': {
                'generated': self.timestamp,
                'total_publications': len(publications),
                'sources': list(set(pub['source'] for pub in prepared_data)),
                'export_tool': 'DNB Spytool v1.0'
            },
            'publications': prepared_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(publications)} publications to JSON: {filename}")

class ExcelExporter(BaseExporter):
    """Export publications to Excel format."""
    
    def export(self, publications: List[Dict[str, Any]], filename: str) -> None:
        """Export publications to Excel file with multiple sheets."""
        prepared_data = self.prepare_data(publications)
        
        if not prepared_data:
            raise ValueError("No publications to export")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main data sheet
            df = pd.DataFrame(prepared_data)
            column_order = ['source', 'title', 'authors', 'year', 'journal', 'doi', 
                           'abstract', 'keywords', 'language', 'publisher', 'isbn', 'issn']
            df = df.reindex(columns=column_order)
            df.to_excel(writer, sheet_name='Publications', index=False)
            
            # Summary sheet
            summary_data = self._create_summary(prepared_data)
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Source breakdown sheet
            source_breakdown = self._create_source_breakdown(prepared_data)
            source_df = pd.DataFrame(source_breakdown)
            source_df.to_excel(writer, sheet_name='Source_Breakdown', index=False)
        
        logger.info(f"Exported {len(publications)} publications to Excel: {filename}")
    
    def _create_summary(self, publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create summary statistics."""
        sources = [pub['source'] for pub in publications]
        years = [pub['year'] for pub in publications if pub['year']]
        
        return [
            {'Metric': 'Total Publications', 'Value': len(publications)},
            {'Metric': 'Export Date', 'Value': self.timestamp},
            {'Metric': 'Sources', 'Value': ', '.join(set(sources))},
            {'Metric': 'DNB Publications', 'Value': sources.count('DNB')},
            {'Metric': 'PubMed Publications', 'Value': sources.count('PubMed')},
            {'Metric': 'Year Range', 'Value': f"{min(years)} - {max(years)}" if years else "N/A"},
            {'Metric': 'Publications with DOI', 'Value': sum(1 for pub in publications if pub['doi'])},
            {'Metric': 'Publications with Abstract', 'Value': sum(1 for pub in publications if pub['abstract'])}
        ]
    
    def _create_source_breakdown(self, publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create source-specific breakdown."""
        breakdown = []
        
        for source in set(pub['source'] for pub in publications):
            source_pubs = [pub for pub in publications if pub['source'] == source]
            years = [pub['year'] for pub in source_pubs if pub['year']]
            
            breakdown.append({
                'Source': source,
                'Publications': len(source_pubs),
                'Percentage': f"{(len(source_pubs) / len(publications)) * 100:.1f}%",
                'Year Range': f"{min(years)} - {max(years)}" if years else "N/A",
                'With DOI': sum(1 for pub in source_pubs if pub['doi']),
                'With Abstract': sum(1 for pub in source_pubs if pub['abstract'])
            })
        
        return breakdown

class ReportExporter(BaseExporter):
    """Export comprehensive PDF reports with analytics."""
    
    def export_report(self, publications: List[Dict[str, Any]], filename: str) -> None:
        """Generate a comprehensive PDF report."""
        if not publications:
            raise ValueError("No publications to generate report from")
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Title
        story.append(Paragraph("DNB Spytool - Publication Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Metadata
        story.append(Paragraph("Report Information", heading_style))
        metadata_data = [
            ['Generated:', self.timestamp],
            ['Total Publications:', str(len(publications))],
            ['Sources:', ', '.join(set(pub.get('source', 'Unknown') for pub in publications))],
            ['Tool Version:', 'DNB Spytool v1.0']
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", heading_style))
        summary_stats = self._generate_summary_stats(publications)
        
        stats_data = [['Metric', 'Value']]
        for stat in summary_stats:
            stats_data.append([stat['metric'], str(stat['value'])])
        
        stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 30))
        
        # Generate and embed charts
        story.extend(self._generate_report_charts(publications))
        
        # Source breakdown
        story.append(Paragraph("Source Breakdown", heading_style))
        source_breakdown = self._generate_source_breakdown(publications)
        
        source_data = [['Source', 'Publications', 'Percentage', 'Year Range']]
        for breakdown in source_breakdown:
            source_data.append([
                breakdown['source'],
                str(breakdown['count']),
                f"{breakdown['percentage']:.1f}%",
                breakdown['year_range']
            ])
        
        source_table = Table(source_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
        source_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(source_table)
          # Build PDF
        doc.build(story)
        logger.info(f"Generated comprehensive report: {filename}")
    
    def _generate_summary_stats(self, publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate summary statistics for the report."""
        # Handle years safely - support both string and int years
        years = []
        for pub in publications:
            year = pub.get('year', '')
            if isinstance(year, int):
                years.append(year)
            elif isinstance(year, str) and year.isdigit():
                years.append(int(year))
            # Skip invalid years
        
        sources = [pub.get('source', 'Unknown') for pub in publications]
        
        stats = [
            {'metric': 'Total Publications', 'value': len(publications)},
            {'metric': 'Unique Sources', 'value': len(set(sources))},
            {'metric': 'DNB Publications', 'value': sources.count('DNB')},
            {'metric': 'PubMed Publications', 'value': sources.count('PubMed')},
            {'metric': 'Publications with DOI', 'value': sum(1 for pub in publications if pub.get('doi'))},
            {'metric': 'Publications with Abstract', 'value': sum(1 for pub in publications if pub.get('abstract'))},
            {'metric': 'Earliest Publication', 'value': min(years) if years else 'N/A'},
            {'metric': 'Latest Publication', 'value': max(years) if years else 'N/A'},
            {'metric': 'Average Publications per Year', 'value': f"{len(years) / len(set(years)):.1f}" if years else 'N/A'}
        ]
        
        return stats
    
    def _generate_source_breakdown(self, publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate source-specific breakdown."""
        breakdown = []
        total_pubs = len(publications)
        for source in set(pub.get('source', 'Unknown') for pub in publications):
            source_pubs = [pub for pub in publications if pub.get('source') == source]
            # Handle years safely - support both string and int years
            years = []
            for pub in source_pubs:
                year = pub.get('year', '')
                if isinstance(year, int):
                    years.append(year)
                elif isinstance(year, str) and year.isdigit():
                    years.append(int(year))
                # Skip invalid years
            
            breakdown.append({
                'source': source,
                'count': len(source_pubs),
                'percentage': (len(source_pubs) / total_pubs) * 100,
                'year_range': f"{min(years)} - {max(years)}" if years else "N/A"
            })
        
        return sorted(breakdown, key=lambda x: x['count'], reverse=True)
    
    def _generate_report_charts(self, publications: List[Dict[str, Any]]) -> List:
        """Generate and embed charts in the report."""
        from .visualizer import PublicationVisualizer
        
        story_elements = []
        visualizer = PublicationVisualizer()
        
        try:
            # Publications by year chart
            story_elements.append(Paragraph("Publications by Year", 
                                          ParagraphStyle('ChartHeading', parent=getSampleStyleSheet()['Heading3'])))
            
            year_chart_path = self._create_temp_chart(visualizer.plot_publications_by_year, publications, "year_chart.png")
            if year_chart_path and os.path.exists(year_chart_path):
                story_elements.append(Image(year_chart_path, width=6*inch, height=4*inch))
                story_elements.append(Spacer(1, 20))
            
            # Publications by source chart
            story_elements.append(Paragraph("Publications by Source", 
                                          ParagraphStyle('ChartHeading', parent=getSampleStyleSheet()['Heading3'])))
            
            source_chart_path = self._create_temp_chart(visualizer.plot_publications_by_source, publications, "source_chart.png")
            if source_chart_path and os.path.exists(source_chart_path):
                story_elements.append(Image(source_chart_path, width=6*inch, height=4*inch))
                story_elements.append(Spacer(1, 20))
            
        except Exception as e:
            logger.warning(f"Could not generate charts for report: {e}")
            story_elements.append(Paragraph("Charts could not be generated due to technical limitations.", 
                                          getSampleStyleSheet()['Normal']))
        
        return story_elements
    
    def _create_temp_chart(self, chart_function, publications: List[Dict[str, Any]], filename: str) -> Optional[str]:
        """Create a temporary chart file for embedding in PDF."""
        try:
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            chart_path = os.path.join(temp_dir, filename)
            
            # Generate chart
            chart_function(publications, save_path=chart_path)
            
            return chart_path if os.path.exists(chart_path) else None
            
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to create temporary chart {filename}: {e}")
            return None