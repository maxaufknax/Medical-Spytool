import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from collections import Counter
import seaborn as sns

logger = logging.getLogger(__name__)

class PublicationVisualizer:
    """Create visualizations and analytics for publication data."""
    
    def __init__(self):
        # Set matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
        
    def plot_publications_by_year(self, publications: List[Dict[str, Any]], 
                                 save_path: Optional[str] = None, 
                                 show_sources: bool = True) -> Optional[str]:
        """
        Create a bar plot of publications by year, optionally split by source.
        
        Args:
            publications: List of publication dictionaries
            save_path: Optional path to save the plot
            show_sources: Whether to show breakdown by source
            
        Returns:
            Path to saved plot or None
        """
        if not publications:
            logger.warning("No publications provided for year visualization")
            return None
        
        # Extract years and sources
        year_data = []
        for pub in publications:
            year = pub.get('year', '')
            source = pub.get('source', 'Unknown')
            if year and str(year).isdigit():
                year_data.append({'year': int(year), 'source': source})
        
        if not year_data:
            logger.warning("No valid year data found for visualization")
            return None
        
        df = pd.DataFrame(year_data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if show_sources and len(df['source'].unique()) > 1:
            # Create stacked bar chart by source
            pivot_df = df.groupby(['year', 'source']).size().unstack(fill_value=0)
            pivot_df.plot(kind='bar', stacked=True, ax=ax, 
                         title='Publications by Year and Source')
            ax.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            # Simple bar chart
            year_counts = df['year'].value_counts().sort_index()
            year_counts.plot(kind='bar', ax=ax, title='Publications by Year')
            ax.set_xlabel('Year')
            ax.set_ylabel('Number of Publications')
        
        # Formatting
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of Publications')
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Publications by year chart saved to: {save_path}")
            return save_path
        else:
            plt.show()
            return None
    
    def plot_publications_by_source(self, publications: List[Dict[str, Any]], 
                                   save_path: Optional[str] = None) -> Optional[str]:
        """
        Create a pie chart of publications by source.
        
        Args:
            publications: List of publication dictionaries
            save_path: Optional path to save the plot
            
        Returns:
            Path to saved plot or None
        """
        if not publications:
            logger.warning("No publications provided for source visualization")
            return None
        
        # Count publications by source
        sources = [pub.get('source', 'Unknown') for pub in publications]
        source_counts = Counter(sources)
        
        if not source_counts:
            logger.warning("No source data found for visualization")
            return None
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        
        labels = list(source_counts.keys())
        sizes = list(source_counts.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
        
        ax.set_title('Publications by Source', fontsize=16, fontweight='bold')
        
        # Add total count
        total = sum(sizes)
        ax.text(0, -1.3, f'Total Publications: {total}', 
                ha='center', fontsize=12, style='italic')
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Publications by source chart saved to: {save_path}")
            return save_path
        else:
            plt.show()
            return None
    
    def plot_top_keywords(self, publications: List[Dict[str, Any]], 
                         top_n: int = 20, save_path: Optional[str] = None) -> Optional[str]:
        """
        Create a horizontal bar chart of top keywords across all sources.
        
        Args:
            publications: List of publication dictionaries
            top_n: Number of top keywords to display
            save_path: Optional path to save the plot
            
        Returns:
            Path to saved plot or None
        """
        if not publications:
            logger.warning("No publications provided for keywords visualization")
            return None
        
        # Extract and count keywords
        all_keywords = []
        for pub in publications:
            keywords = pub.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [kw.strip() for kw in keywords.split(';') if kw.strip()]
            elif isinstance(keywords, list):
                keywords = [str(kw).strip() for kw in keywords if str(kw).strip()]
            
            all_keywords.extend(keywords)
        
        if not all_keywords:
            logger.warning("No keywords found for visualization")
            return None
        
        # Count keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(top_n)
        
        if not top_keywords:
            return None
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(top_keywords) * 0.4)))
        
        keywords, counts = zip(*top_keywords)
        y_pos = range(len(keywords))
        
        bars = ax.barh(y_pos, counts, color=plt.cm.viridis(np.linspace(0, 1, len(keywords))))
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(keywords)
        ax.invert_yaxis()
        ax.set_xlabel('Frequency')
        ax.set_title(f'Top {len(keywords)} Keywords', fontsize=16, fontweight='bold')
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height()/2, 
                   str(count), ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Top keywords chart saved to: {save_path}")
            return save_path
        else:
            plt.show()
            return None
    
    def plot_publications_timeline(self, publications: List[Dict[str, Any]], 
                                  save_path: Optional[str] = None) -> Optional[str]:
        """
        Create a timeline plot showing publication trends by source.
        
        Args:
            publications: List of publication dictionaries
            save_path: Optional path to save the plot
            
        Returns:
            Path to saved plot or None
        """
        if not publications:
            logger.warning("No publications provided for timeline visualization")
            return None
        
        # Extract year and source data
        timeline_data = []
        for pub in publications:
            year = pub.get('year', '')
            source = pub.get('source', 'Unknown')
            if year and str(year).isdigit():
                timeline_data.append({'year': int(year), 'source': source})
        
        if not timeline_data:
            logger.warning("No valid timeline data found")
            return None
        
        df = pd.DataFrame(timeline_data)
        
        # Create line plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot line for each source
        for source in df['source'].unique():
            source_data = df[df['source'] == source]
            year_counts = source_data['year'].value_counts().sort_index()
            
            # Fill missing years with 0
            min_year, max_year = df['year'].min(), df['year'].max()
            full_years = range(min_year, max_year + 1)
            year_counts = year_counts.reindex(full_years, fill_value=0)
            
            ax.plot(year_counts.index, year_counts.values, 
                   marker='o', linewidth=2, label=source, markersize=4)
        
        ax.set_xlabel('Year')
        ax.set_ylabel('Number of Publications')
        ax.set_title('Publication Timeline by Source', fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Timeline chart saved to: {save_path}")
            return save_path
        else:
            plt.show()
            return None
    
    def generate_summary_statistics(self, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.
        
        Args:
            publications: List of publication dictionaries
            
        Returns:
            Dictionary containing summary statistics
        """
        if not publications:
            return {}
        
        # Basic counts
        total_pubs = len(publications)
        sources = [pub.get('source', 'Unknown') for pub in publications]
        source_counts = Counter(sources)
          # Year analysis - handle both string and int years safely
        years = []
        for pub in publications:
            year = pub.get('year', '')
            if isinstance(year, int):
                years.append(year)
            elif isinstance(year, str) and year.isdigit():
                years.append(int(year))
            # Skip invalid years
        
        # Content analysis
        with_doi = sum(1 for pub in publications if pub.get('doi'))
        with_abstract = sum(1 for pub in publications if pub.get('abstract'))
        with_keywords = sum(1 for pub in publications if pub.get('keywords'))
        
        # Language analysis
        languages = [pub.get('language', 'Unknown') for pub in publications if pub.get('language')]
        language_counts = Counter(languages)
        
        statistics = {
            'total_publications': total_pubs,
            'sources': dict(source_counts),
            'year_range': {
                'earliest': min(years) if years else None,
                'latest': max(years) if years else None,
                'span': max(years) - min(years) + 1 if years else 0
            },
            'content_completeness': {
                'with_doi': with_doi,
                'with_doi_percent': (with_doi / total_pubs) * 100,
                'with_abstract': with_abstract,
                'with_abstract_percent': (with_abstract / total_pubs) * 100,
                'with_keywords': with_keywords,
                'with_keywords_percent': (with_keywords / total_pubs) * 100
            },
            'languages': dict(language_counts.most_common(5)),
            'average_per_year': len(years) / len(set(years)) if years else 0
        }
        
        return statistics
    
    def create_comprehensive_report(self, publications: List[Dict[str, Any]], 
                                  output_dir: str = './reports') -> str:
        """
        Create a comprehensive visualization report with all charts.
        
        Args:
            publications: List of publication dictionaries
            output_dir: Directory to save the report files
            
        Returns:
            Path to the main report directory
        """
        if not publications:
            raise ValueError("No publications provided for report generation")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = os.path.join(output_dir, f"publication_report_{timestamp}")
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate all charts
        charts = {
            'publications_by_year.png': self.plot_publications_by_year,
            'publications_by_source.png': self.plot_publications_by_source,
            'top_keywords.png': self.plot_top_keywords,
            'timeline.png': self.plot_publications_timeline
        }
        
        generated_charts = []
        for filename, chart_function in charts.items():
            try:
                chart_path = os.path.join(report_dir, filename)
                result = chart_function(publications, save_path=chart_path)
                if result:
                    generated_charts.append(filename)
            except Exception as e:
                logger.warning(f"Failed to generate {filename}: {e}")
        
        # Generate summary statistics
        stats = self.generate_summary_statistics(publications)
        stats_path = os.path.join(report_dir, 'summary_statistics.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Comprehensive report generated in: {report_dir}")
        logger.info(f"Generated charts: {', '.join(generated_charts)}")
        
        return report_dir