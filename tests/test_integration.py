"""
Integration tests for the complete DNB Spytool workflow.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from src.api.dnb_client import DNBClient
from src.api.pubmed_client import PubMedClient
from src.core.exporters import CSVExporter, JSONExporter
from src.core.visualizer import PublicationVisualizer


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def mock_dnb_results(self):
        return [
            {
                'source': 'DNB',
                'title': 'DNB Test Publication',
                'authors': ['Test Author'],
                'year': '2023',
                'journal': 'Test Journal',
                'doi': '10.1234/dnb',
                'abstract': 'DNB abstract',
                'keywords': ['keyword1'],
                'language': 'ger',
                'publisher': 'Test Publisher',
                'isbn': '',
                'issn': ''
            }
        ]
    
    @pytest.fixture
    def mock_pubmed_results(self):
        return [
            {
                'source': 'PubMed',
                'title': 'PubMed Test Publication',
                'authors': ['Another Author'],
                'year': '2022',
                'journal': 'Medical Journal',
                'doi': '10.1234/pubmed',
                'abstract': 'PubMed abstract',
                'keywords': ['medical', 'research'],
                'language': 'eng',
                'publisher': 'Medical Publisher',
                'isbn': '',
                'issn': '1234-5678'
            }
        ]
    
    def test_complete_search_and_export_workflow(self, mock_dnb_results, mock_pubmed_results):
        """Test complete workflow from search to export."""
        # Mock API clients
        with patch.object(DNBClient, 'search_publications', return_value=mock_dnb_results):
            with patch.object(PubMedClient, 'search_publications', return_value=mock_pubmed_results):
                
                # Perform searches
                dnb_client = DNBClient()
                pubmed_client = PubMedClient()
                
                dnb_results = dnb_client.search_publications("Test Author")
                pubmed_results = pubmed_client.search_publications("Test Author")
                
                # Combine results
                all_results = dnb_results + pubmed_results
                
                assert len(all_results) == 2
                assert all_results[0]['source'] == 'DNB'
                assert all_results[1]['source'] == 'PubMed'
                
                # Test export
                exporter = CSVExporter()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    filename = f.name
                
                try:
                    exporter.export(all_results, filename)
                    assert os.path.exists(filename)
                    
                    # Verify exported content contains both sources
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                        assert 'DNB' in content
                        assert 'PubMed' in content
                finally:
                    if os.path.exists(filename):
                        os.unlink(filename)
    
    def test_search_export_analytics_workflow(self, mock_dnb_results, mock_pubmed_results):
        """Test workflow including analytics generation."""
        all_results = mock_dnb_results + mock_pubmed_results
        
        # Test analytics
        visualizer = PublicationVisualizer()
        stats = visualizer.generate_summary_statistics(all_results)
        
        assert stats['total_publications'] == 2
        assert 'DNB' in stats['sources']
        assert 'PubMed' in stats['sources']
        assert stats['sources']['DNB'] == 1
        assert stats['sources']['PubMed'] == 1
    
    def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow."""
        # Test with connection errors
        with patch.object(DNBClient, 'search_publications', side_effect=Exception("Connection error")):
            dnb_client = DNBClient()
            
            with pytest.raises(Exception, match="Connection error"):
                dnb_client.search_publications("Test Author")
        
        # Test export with empty data
        exporter = CSVExporter()
        with pytest.raises(ValueError):
            exporter.export([], "test.csv")
    
    def test_data_consistency_across_modules(self, mock_dnb_results, mock_pubmed_results):
        """Test that data structure is consistent across all modules."""
        all_results = mock_dnb_results + mock_pubmed_results
        
        # Test that exporters can handle the data
        csv_exporter = CSVExporter()
        json_exporter = JSONExporter()
        
        csv_prepared = csv_exporter.prepare_data(all_results)
        json_prepared = json_exporter.prepare_data(all_results)
        
        # Both should produce the same prepared data
        assert len(csv_prepared) == len(json_prepared) == 2
        assert csv_prepared[0]['source'] == json_prepared[0]['source']
        assert csv_prepared[1]['source'] == json_prepared[1]['source']
        
        # Test that visualizer can handle the data
        visualizer = PublicationVisualizer()
        stats = visualizer.generate_summary_statistics(all_results)
        assert stats['total_publications'] == 2
