"""
Unit tests for publication analytics functionality.
"""

import unittest
from datetime import datetime
from dnb_spytool.analytics.analyzer import PublicationAnalyzer


class TestPublicationAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PublicationAnalyzer()
        
        # Sample publication data
        self.sample_publications = [
            {
                'title': 'Book 1',
                'authors': ['Author A'],
                'publication_year': 2020,
                'subjects': ['Fiction', 'Literature'],
                'publisher': 'Publisher 1',
                'language': 'ger'
            },
            {
                'title': 'Book 2',
                'authors': ['Author A', 'Author B'],
                'publication_year': 2021,
                'subjects': ['Fiction', 'Drama'],
                'publisher': 'Publisher 2',
                'language': 'ger'
            },
            {
                'title': 'Book 3',
                'authors': ['Author B'],
                'publication_year': 2021,
                'subjects': ['Science', 'Technology'],
                'publisher': 'Publisher 1',
                'language': 'eng'
            },
            {
                'title': 'Book 4',
                'authors': ['Author C'],
                'publication_year': 2022,
                'subjects': ['Fiction'],
                'publisher': 'Publisher 3',
                'language': 'ger'
            }
        ]
        
    def test_generate_summary_statistics(self):
        """Test summary statistics generation."""
        stats = self.analyzer.generate_summary_statistics(self.sample_publications)
        
        self.assertEqual(stats['total_publications'], 4)
        self.assertEqual(stats['unique_authors'], 3)
        self.assertEqual(stats['unique_publishers'], 3)
        self.assertEqual(stats['year_range']['earliest'], 2020)
        self.assertEqual(stats['year_range']['latest'], 2022)
        self.assertEqual(stats['year_range']['span'], 2)
        self.assertEqual(stats['language_distribution']['ger'], 3)
        self.assertEqual(stats['language_distribution']['eng'], 1)
        
    def test_generate_summary_statistics_empty(self):
        """Test summary statistics with empty data."""
        stats = self.analyzer.generate_summary_statistics([])
        
        self.assertEqual(stats['total_publications'], 0)
        self.assertEqual(stats['unique_authors'], 0)
        self.assertEqual(stats['unique_publishers'], 0)
        self.assertIsNone(stats['year_range']['earliest'])
        self.assertIsNone(stats['year_range']['latest'])
        self.assertEqual(stats['year_range']['span'], 0)
        
    def test_analyze_publication_timeline(self):
        """Test publication timeline analysis."""
        timeline = self.analyzer.analyze_publication_timeline(self.sample_publications)
        
        expected = {2020: 1, 2021: 2, 2022: 1}
        self.assertEqual(timeline, expected)
        
    def test_analyze_publication_timeline_empty(self):
        """Test timeline analysis with empty data."""
        timeline = self.analyzer.analyze_publication_timeline([])
        self.assertEqual(timeline, {})
        
    def test_analyze_author_productivity(self):
        """Test author productivity analysis."""
        productivity = self.analyzer.analyze_author_productivity(self.sample_publications)
        
        expected = {
            'Author A': 2,
            'Author B': 2,
            'Author C': 1
        }
        self.assertEqual(productivity, expected)
        
    def test_analyze_collaboration_patterns(self):
        """Test collaboration patterns analysis."""
        patterns = self.analyzer.analyze_collaboration_patterns(self.sample_publications)
        
        # Check collaboration pairs
        expected_pairs = {('Author A', 'Author B'): 1}
        self.assertEqual(patterns['collaboration_pairs'], expected_pairs)
        
        # Check single vs collaborative works
        self.assertEqual(patterns['single_author_works'], 3)
        self.assertEqual(patterns['collaborative_works'], 1)
        self.assertEqual(patterns['collaboration_percentage'], 25.0)
        
    def test_analyze_subject_distribution(self):
        """Test subject distribution analysis."""
        distribution = self.analyzer.analyze_subject_distribution(self.sample_publications)
        
        expected = {
            'Fiction': 3,
            'Literature': 1,
            'Drama': 1,
            'Science': 1,
            'Technology': 1
        }
        self.assertEqual(distribution, expected)
        
    def test_analyze_publisher_distribution(self):
        """Test publisher distribution analysis."""
        distribution = self.analyzer.analyze_publisher_distribution(self.sample_publications)
        
        expected = {
            'Publisher 1': 2,
            'Publisher 2': 1,
            'Publisher 3': 1
        }
        self.assertEqual(distribution, expected)
        
    def test_get_top_subjects(self):
        """Test getting top subjects."""
        top_subjects = self.analyzer.get_top_subjects(self.sample_publications, limit=3)
        
        expected = [
            ('Fiction', 3),
            ('Literature', 1),
            ('Drama', 1)
        ]
        # Check first item and length (order may vary for items with same count)
        self.assertEqual(len(top_subjects), 3)
        self.assertEqual(top_subjects[0], ('Fiction', 3))
        
    def test_get_top_publishers(self):
        """Test getting top publishers."""
        top_publishers = self.analyzer.get_top_publishers(self.sample_publications, limit=2)
        
        expected = [
            ('Publisher 1', 2),
            ('Publisher 2', 1)
        ]
        # Check first item and length
        self.assertEqual(len(top_publishers), 2)
        self.assertEqual(top_publishers[0], ('Publisher 1', 2))
        
    def test_get_most_productive_authors(self):
        """Test getting most productive authors."""
        top_authors = self.analyzer.get_most_productive_authors(self.sample_publications, limit=2)
        
        # Should return authors with highest publication count
        self.assertEqual(len(top_authors), 2)
        # First two authors should have 2 publications each
        self.assertEqual(top_authors[0][1], 2)
        self.assertEqual(top_authors[1][1], 2)
        
    def test_analyze_publication_trends(self):
        """Test publication trends analysis."""
        trends = self.analyzer.analyze_publication_trends(self.sample_publications)
        
        # Check that all analysis methods are included
        self.assertIn('timeline', trends)
        self.assertIn('author_productivity', trends)
        self.assertIn('collaboration_patterns', trends)
        self.assertIn('subject_distribution', trends)
        self.assertIn('publisher_distribution', trends)
        self.assertIn('summary_statistics', trends)
        
        # Verify some specific values
        self.assertEqual(trends['timeline'][2020], 1)
        self.assertEqual(trends['summary_statistics']['total_publications'], 4)
        
    def test_filter_by_year_range(self):
        """Test filtering publications by year range."""
        # Test with specific year range
        filtered = self.analyzer._filter_by_year_range(
            self.sample_publications, 
            start_year=2021, 
            end_year=2021
        )
        
        self.assertEqual(len(filtered), 2)
        for pub in filtered:
            self.assertEqual(pub['publication_year'], 2021)
            
    def test_filter_by_year_range_open_ended(self):
        """Test filtering with open-ended year ranges."""
        # Test with only start year
        filtered = self.analyzer._filter_by_year_range(
            self.sample_publications, 
            start_year=2021
        )
        
        self.assertEqual(len(filtered), 3)  # 2021 and 2022
        
        # Test with only end year
        filtered = self.analyzer._filter_by_year_range(
            self.sample_publications, 
            end_year=2021
        )
        
        self.assertEqual(len(filtered), 3)  # 2020 and 2021
        
    def test_filter_publications_with_missing_year(self):
        """Test filtering publications when some have missing years."""
        publications_with_missing = self.sample_publications + [
            {
                'title': 'Book 5',
                'authors': ['Author D'],
                'publication_year': None,
                'subjects': ['History'],
                'publisher': 'Publisher 4',
                'language': 'ger'
            }
        ]
        
        timeline = self.analyzer.analyze_publication_timeline(publications_with_missing)
        
        # Should only include publications with valid years
        expected = {2020: 1, 2021: 2, 2022: 1}
        self.assertEqual(timeline, expected)


if __name__ == '__main__':
    unittest.main()
