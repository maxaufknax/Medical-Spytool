import pytest
import os
import tempfile
import json
import pandas as pd
from unittest.mock import patch, Mock
from src.core.exporters import CSVExporter, JSONExporter, ExcelExporter, ReportExporter

class TestExporters:
    
    @pytest.fixture
    def sample_publications(self):
        return [
            {
                'source': 'DNB',
                'title': 'Test Publication 1',
                'authors': ['Author A', 'Author B'],
                'year': '2023',
                'journal': 'Test Journal',
                'doi': '10.1234/test1',
                'abstract': 'Test abstract 1',
                'keywords': ['keyword1', 'keyword2'],
                'language': 'eng',
                'publisher': 'Test Publisher',
                'isbn': '',
                'issn': '1234-5678'
            },
            {
                'source': 'PubMed',
                'title': 'Test Publication 2',
                'authors': ['Author C'],
                'year': '2022',
                'journal': 'Another Journal',
                'doi': '10.1234/test2',
                'abstract': 'Test abstract 2',
                'keywords': ['keyword3', 'keyword4'],
                'language': 'ger',
                'publisher': 'Another Publisher',
                'isbn': '978-1234567890',
                'issn': ''
            }
        ]
    
    def test_csv_export(self, sample_publications):
        """Test CSV export functionality."""
        exporter = CSVExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            filename = f.name
        
        try:
            exporter.export(sample_publications, filename)
            
            # Verify file exists and contains data
            assert os.path.exists(filename)
            
            # Read and verify content
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'DNB Spytool Export' in content
                assert 'Test Publication 1' in content
                assert 'Test Publication 2' in content
                assert 'DNB' in content
                assert 'PubMed' in content
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_json_export(self, sample_publications):
        """Test JSON export functionality."""
        exporter = JSONExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filename = f.name
        
        try:
            exporter.export(sample_publications, filename)
            
            # Verify file exists
            assert os.path.exists(filename)
            
            # Read and verify JSON structure
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                assert 'metadata' in data
                assert 'publications' in data
                assert data['metadata']['total_publications'] == 2
                assert 'DNB' in data['metadata']['sources']
                assert 'PubMed' in data['metadata']['sources']
                assert len(data['publications']) == 2
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_excel_export(self, sample_publications):
        """Test Excel export functionality."""
        exporter = ExcelExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
            filename = f.name
        
        try:
            exporter.export(sample_publications, filename)
            
            # Verify file exists
            assert os.path.exists(filename)
            
            # Read and verify Excel content
            xl_file = pd.ExcelFile(filename)
            assert 'Publications' in xl_file.sheet_names
            assert 'Summary' in xl_file.sheet_names
            assert 'Source_Breakdown' in xl_file.sheet_names
            
            # Check main data sheet
            df = pd.read_excel(filename, sheet_name='Publications')
            assert len(df) == 2
            assert 'source' in df.columns
            assert 'title' in df.columns
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_report_export(self, sample_publications):
        """Test PDF report export functionality."""
        exporter = ReportExporter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            filename = f.name
        
        try:
            # Mock the chart generation to avoid matplotlib dependencies in tests
            with patch.object(exporter, '_generate_report_charts', return_value=[]):
                exporter.export_report(sample_publications, filename)
            
            # Verify file exists
            assert os.path.exists(filename)
            
            # Basic file size check (PDF should have content)
            assert os.path.getsize(filename) > 1000
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_empty_publications_handling(self):
        """Test handling of empty publication lists."""
        csv_exporter = CSVExporter()
        json_exporter = JSONExporter()
        excel_exporter = ExcelExporter()
        report_exporter = ReportExporter()
        
        with pytest.raises(ValueError):
            csv_exporter.export([], 'test.csv')
        
        with pytest.raises(ValueError):
            excel_exporter.export([], 'test.xlsx')
        
        with pytest.raises(ValueError):
            report_exporter.export_report([], 'test.pdf')
    
    def test_source_column_present(self, sample_publications):
        """Test that all exports include source column."""
        base_exporter = CSVExporter()
        prepared_data = base_exporter.prepare_data(sample_publications)
        
        for pub in prepared_data:
            assert 'source' in pub
            assert pub['source'] in ['DNB', 'PubMed']
    
    def test_data_preparation(self, sample_publications):
        """Test data preparation functionality."""
        exporter = CSVExporter()
        prepared = exporter.prepare_data(sample_publications)
        
        assert len(prepared) == 2
        
        # Check first publication
        pub1 = prepared[0]
        assert pub1['source'] == 'DNB'
        assert pub1['title'] == 'Test Publication 1'
        assert pub1['authors'] == 'Author A; Author B'  # List converted to string
        assert pub1['keywords'] == 'keyword1; keyword2'  # List converted to string
        
        # Check second publication
        pub2 = prepared[1]
        assert pub2['source'] == 'PubMed'
        assert pub2['title'] == 'Test Publication 2'
        assert pub2['authors'] == 'Author C'
