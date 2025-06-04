"""
Publication data analyzer for generating insights and statistics.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import re


class PublicationAnalyzer:
    """Analyzer for publication data with statistical and trend analysis capabilities."""
    
    def __init__(self, publications: Optional[List[Dict]] = None):
        """
        Initialize analyzer with publication data.
        
        Args:
            publications: List of publication dictionaries (optional)
        """
        # Ensure we always have a valid list
        self.publications = publications if publications is not None else []
        
        # Validate and clean publications data
        if self.publications:
            self.publications = [pub for pub in self.publications if pub is not None]
        
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Create a pandas DataFrame from publication data."""
        if not self.publications:
            return pd.DataFrame()
        
        # Flatten the data for analysis
        flattened_data = []
        for pub in self.publications:
            # Skip None or invalid publications
            if not pub or not isinstance(pub, dict):
                continue
                
            # Handle different data structures - convert strings to lists where needed
            authors = pub.get('authors') or pub.get('author', '')
            if authors is None:
                authors_list = []
            elif isinstance(authors, str):
                authors_list = [authors] if authors else []
            elif isinstance(authors, list):
                authors_list = [str(a) for a in authors if a is not None] if authors else []
            else:
                authors_list = []
            
            subjects = pub.get('subjects') or pub.get('subject', '') or pub.get('subject_headings', '')
            if subjects is None:
                subjects_list = []
            elif isinstance(subjects, str):
                subjects_list = [subjects] if subjects else []
            elif isinstance(subjects, list):
                subjects_list = [str(s) for s in subjects if s is not None] if subjects else []
            else:
                subjects_list = []
            
            languages = pub.get('language', '')
            if languages is None:
                languages_list = []
            elif isinstance(languages, str):
                languages_list = [languages] if languages else []
            elif isinstance(languages, list):
                languages_list = [str(l) for l in languages if l is not None] if languages else []
            else:
                languages_list = []
                
            isbn = pub.get('isbn', '')
            if isbn is None:
                isbn_list = []
            elif isinstance(isbn, str):
                isbn_list = [isbn] if isbn else []
            elif isinstance(isbn, list):
                isbn_list = [str(i) for i in isbn if i is not None] if isbn else []
            else:
                isbn_list = []
                
            urls = pub.get('url', '')
            if urls is None:
                urls_list = []
            elif isinstance(urls, str):
                urls_list = [urls] if urls else []
            elif isinstance(urls, list):
                urls_list = [str(u) for u in urls if u is not None] if urls else []
            else:
                urls_list = []
            
            flat_pub = {
                'id': str(pub.get('id', '') or ''),
                'title': str(pub.get('title', '') or ''),
                'author_primary': authors_list[0] if authors_list else '',
                'author_count': len(authors_list),
                'authors': ', '.join(authors_list),
                'publication_year': pub.get('publication_year') or pub.get('year'),
                'publisher': str(pub.get('publisher', '') or ''),
                'isbn_count': len(isbn_list),
                'subject_count': len(subjects_list),
                'subjects': ', '.join(subjects_list),
                'language_count': len(languages_list),
                'languages': ', '.join(languages_list),
                'type': str(pub.get('type', '') or pub.get('publication_type', '') or ''),
                'has_url': len(urls_list) > 0,
                'description': str(pub.get('description', '') or pub.get('abstract', '') or ''),
                'title_length': len(str(pub.get('title', '') or '')),
                'has_isbn': len(isbn_list) > 0,
                'database_source': str(pub.get('database_source', 'Unknown') or 'Unknown')
            }
            flattened_data.append(flat_pub)
        
        df = pd.DataFrame(flattened_data)
        
        # Convert year to datetime for better analysis
        if 'publication_year' in df.columns:
            df['publication_year'] = pd.to_numeric(df['publication_year'], errors='coerce')
        
        return df
    
    def get_basic_statistics(self) -> Dict:
        """Get basic statistics about the publication data."""
        if self.df.empty:
            return {
                'total_publications': 0,
                'unique_authors': 0,
                'date_range': {'earliest': None, 'latest': None, 'span_years': 0},
                'publication_types': {},
                'language_distribution': {},
                'publications_with_isbn': 0,
                'publications_with_url': 0,
                'average_title_length': 0,
                'most_productive_years': [],
                'top_publishers': [],
                'collaboration_stats': {
                    'single_author_pubs': 0,
                    'multi_author_pubs': 0,
                    'max_authors_per_pub': 0,
                    'avg_authors_per_pub': 0,
                    'collaboration_rate': 0
                },
                'database_source_distribution': {}
            }
        
        try:
            stats = {
                'total_publications': len(self.df),
                'unique_authors': len(self.df['authors'].str.split(', ').explode().unique()) if 'authors' in self.df.columns and not self.df['authors'].isna().all() else 0,
                'date_range': self._get_date_range(),
                'publication_types': self._get_publication_types(),
                'language_distribution': self._get_language_distribution(),
                'publications_with_isbn': int(self.df['has_isbn'].sum()) if 'has_isbn' in self.df.columns else 0,
                'publications_with_url': int(self.df['has_url'].sum()) if 'has_url' in self.df.columns else 0,
                'average_title_length': float(self.df['title_length'].mean()) if 'title_length' in self.df.columns and not self.df['title_length'].isna().all() else 0,
                'most_productive_years': self._get_most_productive_years(),
                'top_publishers': self._get_top_publishers(),
                'collaboration_stats': self._get_collaboration_stats(),
                'database_source_distribution': self._get_database_source_distribution()
            }
            return stats
        except Exception as e:
            print(f"Error in get_basic_statistics: {e}")
            return {
                'total_publications': len(self.df) if not self.df.empty else 0,
                'unique_authors': 0,
                'date_range': {'earliest': None, 'latest': None, 'span_years': 0},
                'publication_types': {},
                'language_distribution': {},
                'publications_with_isbn': 0,
                'publications_with_url': 0,
                'average_title_length': 0,
                'most_productive_years': [],
                'top_publishers': [],
                'collaboration_stats': {
                    'single_author_pubs': 0,
                    'multi_author_pubs': 0,
                    'max_authors_per_pub': 0,
                    'avg_authors_per_pub': 0,
                    'collaboration_rate': 0
                },
                'database_source_distribution': {}
            }
    
    def _get_database_source_distribution(self) -> Dict:
        """Get distribution of publications by database source."""
        if 'database_source' not in self.df.columns:
            return {}
        
        return self.df['database_source'].value_counts().to_dict()
    
    def _get_date_range(self) -> Dict:
        """Get the date range of publications."""
        if 'publication_year' not in self.df.columns or self.df['publication_year'].isna().all():
            return {'earliest': None, 'latest': None, 'span_years': 0}
        
        valid_years = self.df['publication_year'].dropna()
        if valid_years.empty:
            return {'earliest': None, 'latest': None, 'span_years': 0}
        
        earliest = int(valid_years.min())
        latest = int(valid_years.max())
        
        return {
            'earliest': earliest,
            'latest': latest,
            'span_years': latest - earliest + 1
        }
    
    def _get_publication_types(self) -> Dict:
        """Get distribution of publication types."""
        if 'type' not in self.df.columns:
            return {}
        
        return self.df['type'].value_counts().to_dict()
    
    def _get_language_distribution(self) -> Dict:
        """Get distribution of publication languages."""
        if 'languages' not in self.df.columns:
            return {}
        
        # Split and count individual languages
        all_languages = []
        for langs in self.df['languages'].dropna():
            if langs:
                all_languages.extend([lang.strip() for lang in langs.split(',')])
        
        return dict(Counter(all_languages))
    
    def _get_most_productive_years(self, top_n: int = 5) -> List[Tuple[int, int]]:
        """Get the most productive publication years."""
        if 'publication_year' not in self.df.columns:
            return []
        
        year_counts = self.df['publication_year'].value_counts().head(top_n)
        return [(int(year), int(count)) for year, count in year_counts.items() if pd.notna(year)]
    
    def _get_top_publishers(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most frequent publishers."""
        if 'publisher' not in self.df.columns:
            return []
        
        # Clean publisher names
        publishers = self.df['publisher'].dropna()
        publishers = publishers[publishers != '']
        
        if publishers.empty:
            return []
        
        publisher_counts = publishers.value_counts().head(top_n)
        return [(publisher, int(count)) for publisher, count in publisher_counts.items()]
    
    def _get_collaboration_stats(self) -> Dict:
        """Get statistics about author collaboration."""
        if 'author_count' not in self.df.columns or self.df.empty:
            return {
                'single_author_pubs': 0,
                'multi_author_pubs': 0,
                'max_authors_per_pub': 0,
                'avg_authors_per_pub': 0,
                'collaboration_rate': 0
            }
        
        try:
            author_counts = self.df['author_count'].fillna(0)
            
            return {
                'single_author_pubs': int((author_counts == 1).sum()),
                'multi_author_pubs': int((author_counts > 1).sum()),
                'max_authors_per_pub': int(author_counts.max()) if len(author_counts) > 0 else 0,
                'avg_authors_per_pub': float(author_counts.mean()) if len(author_counts) > 0 else 0,
                'collaboration_rate': float((author_counts > 1).mean()) if len(author_counts) > 0 else 0
            }
        except Exception as e:
            print(f"Error in _get_collaboration_stats: {e}")
            return {
                'single_author_pubs': 0,
                'multi_author_pubs': 0,
                'max_authors_per_pub': 0,
                'avg_authors_per_pub': 0,
                'collaboration_rate': 0
            }
    
    def get_publication_timeline(self, bin_size: str = 'year') -> pd.DataFrame:
        """
        Get publication timeline data for visualization.
        
        Args:
            bin_size: Time bin size ('year', '5year', 'decade')
            
        Returns:
            DataFrame with time periods and publication counts
        """
        if 'publication_year' not in self.df.columns or self.df['publication_year'].isna().all():
            return pd.DataFrame()
        
        valid_data = self.df[self.df['publication_year'].notna()].copy()
        
        if bin_size == 'year':
            timeline = valid_data.groupby('publication_year').size().reset_index(name='count')
            timeline['period'] = timeline['publication_year'].astype(int).astype(str)
        elif bin_size == '5year':
            valid_data['period_start'] = (valid_data['publication_year'] // 5) * 5
            timeline = valid_data.groupby('period_start').size().reset_index(name='count')
            timeline['period'] = timeline['period_start'].astype(int).astype(str) + '-' + (timeline['period_start'] + 4).astype(int).astype(str)
        elif bin_size == 'decade':
            valid_data['period_start'] = (valid_data['publication_year'] // 10) * 10
            timeline = valid_data.groupby('period_start').size().reset_index(name='count')
            timeline['period'] = timeline['period_start'].astype(int).astype(str) + 's'
        else:
            raise ValueError("bin_size must be 'year', '5year', or 'decade'")
        
        return timeline.sort_values('period')
    
    def get_subject_analysis(self, top_n: int = 20) -> Dict:
        """
        Analyze subject distribution and trends.
        
        Args:
            top_n: Number of top subjects to return
            
        Returns:
            Dictionary with subject analysis results
        """
        if 'subjects' not in self.df.columns:
            return {}
        
        # Extract all subjects
        all_subjects = []
        for subjects in self.df['subjects'].dropna():
            if subjects:
                all_subjects.extend([subj.strip() for subj in subjects.split(',')])
        
        if not all_subjects:
            return {}
        
        subject_counts = Counter(all_subjects)
        
        # Subject trends over time
        subject_trends = {}
        if 'publication_year' in self.df.columns:
            for year, group in self.df.groupby('publication_year'):
                if pd.isna(year):
                    continue
                year_subjects = []
                for subjects in group['subjects'].dropna():
                    if subjects:
                        year_subjects.extend([subj.strip() for subj in subjects.split(',')])
                
                for subject in set(year_subjects):  # Unique subjects per year
                    if subject not in subject_trends:
                        subject_trends[subject] = {}
                    subject_trends[subject][int(year)] = year_subjects.count(subject)
        
        return {
            'top_subjects': subject_counts.most_common(top_n),
            'total_unique_subjects': len(subject_counts),
            'subject_trends': subject_trends,
            'avg_subjects_per_publication': len(all_subjects) / len(self.df)
        }
    
    def get_author_productivity(self) -> Dict:
        """Analyze author productivity and patterns."""
        if 'authors' not in self.df.columns:
            return {}
        
        # Extract all authors
        author_publications = defaultdict(list)
        
        for idx, row in self.df.iterrows():
            if pd.notna(row['authors']) and row['authors']:
                authors = [author.strip() for author in row['authors'].split(',')]
                for author in authors:
                    if author:
                        author_publications[author].append({
                            'year': row.get('publication_year'),
                            'title': row.get('title', ''),
                            'type': row.get('type', ''),
                            'publisher': row.get('publisher', '')
                        })
        
        # Calculate productivity metrics
        productivity_stats = {}
        for author, pubs in author_publications.items():
            years = [pub['year'] for pub in pubs if pd.notna(pub['year'])]
            
            productivity_stats[author] = {
                'total_publications': len(pubs),
                'years_active': len(set(years)) if years else 0,
                'first_publication': min(years) if years else None,
                'last_publication': max(years) if years else None,
                'avg_publications_per_year': len(pubs) / len(set(years)) if years else 0,
                'publication_types': Counter([pub['type'] for pub in pubs if pub['type']]),
                'publishers': Counter([pub['publisher'] for pub in pubs if pub['publisher']])
            }
        
        # Sort by productivity
        sorted_authors = sorted(productivity_stats.items(), 
                              key=lambda x: x[1]['total_publications'], 
                              reverse=True)
        
        return {
            'author_stats': dict(sorted_authors[:20]),  # Top 20 most productive
            'total_authors': len(author_publications),
            'single_publication_authors': sum(1 for stats in productivity_stats.values() 
                                            if stats['total_publications'] == 1),
            'prolific_authors': sum(1 for stats in productivity_stats.values() 
                                  if stats['total_publications'] >= 5)
        }
    
    def get_network_analysis_data(self) -> Dict:
        """Get data for author collaboration network analysis."""
        if 'authors' not in self.df.columns:
            return {}
        
        # Find collaborations (publications with multiple authors)
        collaborations = []
        author_connections = defaultdict(set)
        
        for _, row in self.df.iterrows():
            if pd.notna(row['authors']) and row['authors']:
                authors = [author.strip() for author in row['authors'].split(',')]
                if len(authors) > 1:
                    # Record all pairs of collaborators
                    for i, author1 in enumerate(authors):
                        for author2 in authors[i+1:]:
                            if author1 and author2:
                                collaborations.append((author1, author2))
                                author_connections[author1].add(author2)
                                author_connections[author2].add(author1)
        
        # Calculate network metrics
        collaboration_counts = Counter(collaborations)
        
        return {
            'collaborations': dict(collaboration_counts),
            'author_connections': {author: list(connections) 
                                 for author, connections in author_connections.items()},
            'total_collaborations': len(collaborations),
            'unique_collaboration_pairs': len(collaboration_counts),
            'most_frequent_collaborations': collaboration_counts.most_common(10)
        }
    
    def generate_summary_report(self) -> str:
        """Generate a text summary report of the analysis."""
        if self.df.empty:
            return "No publication data available for analysis."
        
        stats = self.get_basic_statistics()
        
        report = f"""
=== DNB PUBLICATION ANALYSIS REPORT ===

OVERVIEW:
- Total Publications: {stats['total_publications']:,}
- Unique Authors: {stats['unique_authors']:,}
- Time Span: {stats['date_range']['earliest']} - {stats['date_range']['latest']} ({stats['date_range']['span_years']} years)

PUBLICATION CHARACTERISTICS:
- Publications with ISBN: {stats['publications_with_isbn']:,} ({stats['publications_with_isbn']/stats['total_publications']*100:.1f}%)
- Publications with URL: {stats['publications_with_url']:,} ({stats['publications_with_url']/stats['total_publications']*100:.1f}%)
- Average Title Length: {stats['average_title_length']:.1f} characters

COLLABORATION:
- Single Author Publications: {stats['collaboration_stats']['single_author_pubs']:,}
- Multi-Author Publications: {stats['collaboration_stats']['multi_author_pubs']:,}
- Collaboration Rate: {stats['collaboration_stats']['collaboration_rate']*100:.1f}%
- Max Authors per Publication: {stats['collaboration_stats']['max_authors_per_pub']}

MOST PRODUCTIVE YEARS:
"""
        
        for year, count in stats['most_productive_years'][:5]:
            report += f"- {year}: {count:,} publications\n"
        
        report += "\nTOP PUBLISHERS:\n"
        for publisher, count in stats['top_publishers'][:5]:
            report += f"- {publisher}: {count:,} publications\n"
        
        report += "\nPUBLICATION TYPES:\n"
        for pub_type, count in list(stats['publication_types'].items())[:5]:
            report += f"- {pub_type}: {count:,} publications\n"
        
        report += "\nLANGUAGE DISTRIBUTION:\n"
        for language, count in list(stats['language_distribution'].items())[:5]:
            report += f"- {language}: {count:,} publications\n"
        
        # Add database source information if available
        if stats.get('database_source_distribution'):
            report += "\nDATABASE SOURCES:\n"
            for source, count in stats['database_source_distribution'].items():
                percentage = (count / stats['total_publications']) * 100
                report += f"- {source.upper()}: {count:,} publications ({percentage:.1f}%)\n"
            
            if len(stats['database_source_distribution']) > 1:
                report += "\n🔍 Multi-Database Search Results: Data from multiple sources combined\n"
        
        return report
    
    def generate_summary_statistics(self, publications: List[Dict]) -> Dict:
        """Generate summary statistics for publications."""
        if not publications:
            return {
                'total_publications': 0,
                'unique_authors': 0,
                'unique_publishers': 0,
                'year_range': {'earliest': None, 'latest': None, 'span': 0},
                'language_distribution': {}
            }
        
        # Extract data
        all_authors = set()
        all_publishers = set()
        years = []
        languages = []
        
        for pub in publications:
            # Authors
            authors = pub.get('authors', [])
            if isinstance(authors, str):
                authors = [authors]
            for author in authors:
                if author:
                    all_authors.add(author.strip())
            
            # Publishers
            publisher = pub.get('publisher')
            if publisher:
                all_publishers.add(publisher.strip())
            
            # Years
            year = pub.get('publication_year')
            if year:
                try:
                    years.append(int(year))
                except (ValueError, TypeError):
                    pass
            
            # Languages
            lang = pub.get('language')
            if lang:
                languages.append(lang)
        
        # Calculate statistics
        stats = {
            'total_publications': len(publications),
            'unique_authors': len(all_authors),
            'unique_publishers': len(all_publishers),
            'year_range': {
                'earliest': min(years) if years else None,
                'latest': max(years) if years else None,
                'span': (max(years) - min(years)) if years else 0
            },
            'language_distribution': dict(Counter(languages))        }
        
        return stats
    
    def analyze_publication_timeline(self, publications: List[Dict]) -> Dict:
        """Analyze publication timeline."""
        if not publications:
            return {}
        
        years = []
        for pub in publications:
            year = pub.get('publication_year')
            if year:
                try:
                    years.append(int(year))
                except (ValueError, TypeError):
                    pass
        
        if not years:
            return {}
        
        year_counts = Counter(years)
        return dict(year_counts)
    
    def analyze_author_productivity(self, publications: List[Dict]) -> Dict:
        """Analyze author productivity."""
        if not publications:
            return {}
        
        author_counts = Counter()
        
        for pub in publications:
            authors = pub.get('authors', [])
            if isinstance(authors, str):
                authors = [authors]
            
            for author in authors:
                if author:
                    clean_author = author.strip()
                    author_counts[clean_author] += 1
        
        return dict(author_counts)
    
    def analyze_collaboration_patterns(self, publications: List[Dict]) -> Dict:
        """Analyze collaboration patterns."""
        if not publications:
            return {}
        
        single_author = 0
        multi_author = 0
        collaborations = []
        
        for pub in publications:
            authors = pub.get('authors', [])
            if isinstance(authors, str):
                authors = [authors]
            
            author_count = len([a for a in authors if a and a.strip()])
            
            if author_count == 1:
                single_author += 1
            elif author_count > 1:
                multi_author += 1
                # Record collaboration pairs
                clean_authors = [a.strip() for a in authors if a and a.strip()]
                for i in range(len(clean_authors)):
                    for j in range(i+1, len(clean_authors)):
                        collaborations.append(tuple(sorted([clean_authors[i], clean_authors[j]])))
        
        collaboration_counts = Counter(collaborations)
        
        return {
            'collaboration_pairs': dict(collaboration_counts),
            'single_author_works': single_author,
            'collaborative_works': multi_author,
            'collaboration_percentage': (multi_author / len(publications)) * 100 if publications else 0
        }
    
    def analyze_publication_trends(self, publications: List[Dict]) -> Dict:
        """Analyze publication trends over time."""
        if not publications:
            return {
                'timeline': {},
                'author_productivity': {},
                'collaboration_patterns': {},
                'subject_distribution': {},
                'publisher_distribution': {},
                'summary_statistics': {
                    'total_publications': 0,
                    'unique_authors': 0,
                    'unique_publishers': 0
                }
            }
        
        return {
            'timeline': self.analyze_publication_timeline(publications),
                        'author_productivity': self.analyze_author_productivity(publications),
            'collaboration_patterns': self.analyze_collaboration_patterns(publications),
            'subject_distribution': self.analyze_subject_distribution(publications),
            'publisher_distribution': self.analyze_publisher_distribution(publications),
            'summary_statistics': self.generate_summary_statistics(publications)
        }
    
    def analyze_publisher_distribution(self, publications: List[Dict]) -> Dict:
        """Analyze publisher distribution."""
        if not publications:
            return {}
        
        publishers = []
        for pub in publications:
            publisher = pub.get('publisher', 'Unknown')
            if publisher:
                publishers.append(publisher.strip())
        
        if not publishers:
            return {}
        
        publisher_counts = Counter(publishers)
        return dict(publisher_counts)
    
    def analyze_subject_distribution(self, publications: List[Dict]) -> Dict:
        """Analyze subject distribution."""
        if not publications:
            return {}
        
        all_subjects = []
        for pub in publications:
            subjects = pub.get('subjects', [])
            if isinstance(subjects, str):
                subjects = [subjects]
            for subject in subjects:
                if subject:
                    all_subjects.append(subject.strip())
        
        if not all_subjects:
            return {}
        
        subject_counts = Counter(all_subjects)
        return dict(subject_counts)

    def get_top_subjects(self, publications: List[Dict], limit: int = 10) -> List[Tuple[str, int]]:
        """Get top subjects by count."""
        all_subjects = []
        for pub in publications:
            subjects = pub.get('subjects', [])
            if isinstance(subjects, str):
                subjects = [subjects]
            for subject in subjects:
                if subject:
                    all_subjects.append(subject.strip())
        
        if not all_subjects:
            return []
        
        return Counter(all_subjects).most_common(limit)

    def get_top_publishers(self, publications: List[Dict], limit: int = 10) -> List[Tuple[str, int]]:
        """Get top publishers by count."""
        publishers = []
        for pub in publications:
            publisher = pub.get('publisher', 'Unknown')
            if publisher:
                publishers.append(publisher.strip())
        
        if not publishers:
            return []
        
        return Counter(publishers).most_common(limit)

    def get_most_productive_authors(self, publications: List[Dict], limit: int = 10) -> List[Tuple[str, int]]:
        """Get most productive authors by publication count."""
        author_counts = Counter()
        
        for pub in publications:
            authors = pub.get('authors', [])
            if isinstance(authors, str):
                authors = [authors]
            
            for author in authors:
                if author:
                    author_counts[author.strip()] += 1
        
        return author_counts.most_common(limit)

    def _filter_by_year_range(self, publications: List[Dict], start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
        """Filter publications by year range."""
        if not publications:
            return []
        
        filtered = []
        for pub in publications:
            year = pub.get('publication_year')
            if year:
                try:
                    year_int = int(year)
                    if start_year is not None and year_int < start_year:
                        continue
                    if end_year is not None and year_int > end_year:
                        continue
                    filtered.append(pub)
                except (ValueError, TypeError):
                    # Include publications with invalid years if no filtering needed
                    if start_year is None and end_year is None:
                        filtered.append(pub)
            else:
                # Include publications without years if no filtering needed
                if start_year is None and end_year is None:
                    filtered.append(pub)
        
        return filtered
