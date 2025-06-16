import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from src.core.visualizer import PublicationVisualizer

class TestPublicationVisualizer:
    
    @pytest.fixture
    def sample_publications(self):
        return [
            {
                'source': 'DNB',
                'title': 'Test Publication 1',
                'year': '2023',
                'keywords': ['machine learning', 'AI'],
            },
            {
                'source': 'PubMed',
                'title': 'Test Publication 2',
                'year': '2022',
                'keywords': ['deep learning', 'neural networks'],
            },
            {
                'source': 'DNB',
                'title': 'Test Publication 3',
                'year': '2023',
                'keywords': ['machine learning', 'data science'],
            }
        ]
    
    @pytest.fixture
    def visualizer(self):
        return PublicationVisualizer()
    
    def test_plot_publications_by_year(self, visualizer, sample_publications):
        """Test year-based visualization."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            filename = f.name
        
        try:
            with patch('matplotlib.pyplot.savefig'), patch('matplotlib.pyplot.close'):
                result = visualizer.plot_publications_by_year(
                    sample_publications, save_path=filename
                )
                assert result == filename
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_plot_publications_by_source(self, visualizer, sample_publications):
        """Test source-based visualization."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            filename = f.name
        
        try:
            with patch('matplotlib.pyplot.savefig'), patch('matplotlib.pyplot.close'):
                result = visualizer.plot_publications_by_source(
                    sample_publications, save_path=filename
                )
                assert result == filename
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_plot_top_keywords(self, visualizer, sample_publications):
        """Test keywords visualization."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            filename = f.name
        
        try:
            with patch('matplotlib.pyplot.savefig'), patch('matplotlib.pyplot.close'):
                result = visualizer.plot_top_keywords(
                    sample_publications, save_path=filename
                )
                assert result == filename
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_generate_summary_statistics(self, visualizer, sample_publications):
        """Test summary statistics generation."""
        stats = visualizer.generate_summary_statistics(sample_publications)
        
        assert stats['total_publications'] == 3
        assert 'DNB' in stats['sources']
        assert 'PubMed' in stats['sources']
        assert stats['sources']['DNB'] == 2
        assert stats['sources']['PubMed'] == 1
        assert stats['year_range']['earliest'] == 2022
        assert stats['year_range']['latest'] == 2023
    
    def test_empty_publications_handling(self, visualizer):
        """Test handling of empty publication lists."""
        result = visualizer.plot_publications_by_year([])
        assert result is None
        
        result = visualizer.plot_publications_by_source([])
        assert result is None
        
        result = visualizer.plot_top_keywords([])
        assert result is None
        
        stats = visualizer.generate_summary_statistics([])
        assert stats == {}
    
    def test_invalid_year_data(self, visualizer):
        """Test handling of invalid year data."""
        invalid_data = [
            {'source': 'DNB', 'year': 'invalid', 'title': 'Test'},
            {'source': 'PubMed', 'year': '', 'title': 'Test 2'}
        ]
        
        result = visualizer.plot_publications_by_year(invalid_data)
        assert result is None
