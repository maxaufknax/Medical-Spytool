"""
Visualization module for creating charts and graphs from publication data.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import os


class PublicationVisualizer:
    """Creates visualizations for publication data analysis."""
    
    def __init__(self, analyzer=None, style: str = 'seaborn-v0_8'):
        """
        Initialize the visualizer.
        
        Args:
            analyzer: PublicationAnalyzer instance
            style: Matplotlib style to use
        """
        self.analyzer = analyzer
        plt.style.use('default')  # Use default style as seaborn styles may not be available
        sns.set_palette("husl")
        
        # Set default figure parameters
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
    
    def create_publication_timeline(self, bin_size: str = 'year', 
                                  save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a timeline visualization of publications over time.
        
        Args:
            bin_size: Time bin size ('year', '5year', 'decade')
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        timeline_data = self.analyzer.get_publication_timeline(bin_size)
        
        if timeline_data.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No temporal data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Publication Timeline')
            return fig
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create bar plot
        bars = ax.bar(range(len(timeline_data)), timeline_data['count'], 
                     color='steelblue', alpha=0.7, edgecolor='navy', linewidth=0.5)
        
        # Customize the plot
        ax.set_xlabel(f'Time Period ({bin_size})')
        ax.set_ylabel('Number of Publications')
        ax.set_title('Publication Timeline', fontsize=16, fontweight='bold')
        
        # Set x-axis labels
        ax.set_xticks(range(len(timeline_data)))
        ax.set_xticklabels(timeline_data['period'], rotation=45 if len(timeline_data) > 10 else 0)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # Add trend line if enough data points
        if len(timeline_data) > 3:
            x_numeric = range(len(timeline_data))
            z = np.polyfit(x_numeric, timeline_data['count'], 1)
            p = np.poly1d(z)
            ax.plot(x_numeric, p(x_numeric), "r--", alpha=0.8, linewidth=2, label='Trend')
            ax.legend()
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_author_productivity_chart(self, top_n: int = 15, 
                                       save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a horizontal bar chart of author productivity.
        
        Args:
            top_n: Number of top authors to display
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        productivity_data = self.analyzer.get_author_productivity()
        
        if not productivity_data.get('author_stats'):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No author data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Author Productivity')
            return fig
        
        # Get top authors
        top_authors = list(productivity_data['author_stats'].items())[:top_n]
        authors = [author for author, _ in top_authors]
        pub_counts = [stats['total_publications'] for _, stats in top_authors]
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(authors) * 0.4)))
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(authors)), pub_counts, 
                      color='darkgreen', alpha=0.7, edgecolor='darkgreen')
        
        # Customize the plot
        ax.set_yticks(range(len(authors)))
        ax.set_yticklabels([author[:50] + '...' if len(author) > 50 else author 
                           for author in authors])
        ax.set_xlabel('Number of Publications')
        ax.set_title(f'Top {len(authors)} Most Productive Authors', fontsize=16, fontweight='bold')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                   f'{int(width)}', ha='left', va='center', fontsize=9)
        
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_subject_wordcloud_chart(self, top_n: int = 20, 
                                     save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a bar chart of top subjects (alternative to word cloud).
        
        Args:
            top_n: Number of top subjects to display
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        subject_data = self.analyzer.get_subject_analysis(top_n)
        
        if not subject_data.get('top_subjects'):
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No subject data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Subject Distribution')
            return fig
        
        subjects, counts = zip(*subject_data['top_subjects'])
        
        fig, ax = plt.subplots(figsize=(12, max(8, len(subjects) * 0.3)))
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(subjects)), counts, 
                      color='purple', alpha=0.7, edgecolor='darkviolet')
        
        # Customize the plot
        ax.set_yticks(range(len(subjects)))
        ax.set_yticklabels([subj[:60] + '...' if len(subj) > 60 else subj 
                           for subj in subjects])
        ax.set_xlabel('Frequency')
        ax.set_title(f'Top {len(subjects)} Subject Areas', fontsize=16, fontweight='bold')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                   f'{int(width)}', ha='left', va='center', fontsize=9)
        
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_publication_type_pie_chart(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a pie chart of publication types.
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        stats = self.analyzer.get_basic_statistics()
        pub_types = stats.get('publication_types', {})
        
        if not pub_types:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, 'No publication type data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Publication Types')
            return fig
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get top types (combine small categories into "Others")
        sorted_types = sorted(pub_types.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_types) > 8:
            top_types = sorted_types[:7]
            others_count = sum(count for _, count in sorted_types[7:])
            top_types.append(('Others', others_count))
        else:
            top_types = sorted_types
        
        labels, sizes = zip(*top_types)
        
        # Create pie chart with custom colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                         startangle=90, colors=colors,
                                         explode=[0.05] * len(labels))
        
        # Beautify the chart
        ax.set_title('Distribution of Publication Types', fontsize=16, fontweight='bold')
        
        # Improve text formatting
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_collaboration_analysis(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create visualization of collaboration patterns.
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        stats = self.analyzer.get_basic_statistics()
        collab_stats = stats.get('collaboration_stats', {})
        
        if not collab_stats:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No collaboration data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Collaboration Analysis')
            return fig
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Collaboration pie chart
        collab_data = [
            collab_stats.get('single_author_pubs', 0),
            collab_stats.get('multi_author_pubs', 0)
        ]
        labels = ['Single Author', 'Multi-Author']
        colors = ['lightcoral', 'lightblue']
        
        wedges, texts, autotexts = ax1.pie(collab_data, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors, explode=[0.05, 0.05])
        ax1.set_title('Single vs Multi-Author Publications', fontweight='bold')
        
        # Author count distribution
        if hasattr(self.analyzer, 'df') and 'author_count' in self.analyzer.df.columns:
            author_counts = self.analyzer.df['author_count'].value_counts().sort_index()
            
            # Limit to reasonable range
            author_counts = author_counts[author_counts.index <= 10]
            
            bars = ax2.bar(author_counts.index, author_counts.values, 
                          color='mediumseagreen', alpha=0.7, edgecolor='darkgreen')
            ax2.set_xlabel('Number of Authors')
            ax2.set_ylabel('Number of Publications')
            ax2.set_title('Distribution by Author Count', fontweight='bold')
            ax2.set_xticks(author_counts.index)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_comprehensive_dashboard(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a comprehensive dashboard with multiple visualizations.
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        fig = plt.figure(figsize=(20, 16))
        
        # Create subplots
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Publication timeline (top row, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        timeline_data = self.analyzer.get_publication_timeline('year')
        if not timeline_data.empty:
            bars = ax1.bar(range(len(timeline_data)), timeline_data['count'], 
                          color='steelblue', alpha=0.7)
            ax1.set_title('Publication Timeline', fontweight='bold')
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Publications')
            ax1.set_xticks(range(0, len(timeline_data), max(1, len(timeline_data)//10)))
            ax1.set_xticklabels([timeline_data.iloc[i]['period'] 
                               for i in range(0, len(timeline_data), max(1, len(timeline_data)//10))],
                               rotation=45)
        
        # 2. Publication types pie chart (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        stats = self.analyzer.get_basic_statistics()
        pub_types = stats.get('publication_types', {})
        if pub_types:
            sorted_types = sorted(pub_types.items(), key=lambda x: x[1], reverse=True)[:6]
            if len(pub_types) > 6:
                others = sum(count for _, count in list(pub_types.items())[6:])
                sorted_types.append(('Others', others))
            
            labels, sizes = zip(*sorted_types)
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Publication Types', fontweight='bold')
        
        # 3. Top authors (middle row, left)
        ax3 = fig.add_subplot(gs[1, 0])
        productivity_data = self.analyzer.get_author_productivity()
        if productivity_data.get('author_stats'):
            top_authors = list(productivity_data['author_stats'].items())[:10]
            authors = [author[:20] + '...' if len(author) > 20 else author 
                      for author, _ in top_authors]
            pub_counts = [stats['total_publications'] for _, stats in top_authors]
            
            ax3.barh(range(len(authors)), pub_counts, color='darkgreen', alpha=0.7)
            ax3.set_yticks(range(len(authors)))
            ax3.set_yticklabels(authors, fontsize=8)
            ax3.set_title('Top Authors', fontweight='bold')
            ax3.set_xlabel('Publications')
        
        # 4. Subject distribution (middle row, center and right)
        ax4 = fig.add_subplot(gs[1, 1:])
        subject_data = self.analyzer.get_subject_analysis(15)
        if subject_data.get('top_subjects'):
            subjects, counts = zip(*subject_data['top_subjects'])
            subjects = [subj[:40] + '...' if len(subj) > 40 else subj for subj in subjects]
            
            bars = ax4.barh(range(len(subjects)), counts, color='purple', alpha=0.7)
            ax4.set_yticks(range(len(subjects)))
            ax4.set_yticklabels(subjects, fontsize=8)
            ax4.set_title('Top Subject Areas', fontweight='bold')
            ax4.set_xlabel('Frequency')
        
        # 5. Collaboration analysis (bottom row, left)
        ax5 = fig.add_subplot(gs[2, 0])
        collab_stats = stats.get('collaboration_stats', {})
        if collab_stats:
            collab_data = [
                collab_stats.get('single_author_pubs', 0),
                collab_stats.get('multi_author_pubs', 0)
            ]
            labels = ['Single', 'Multi']
            ax5.pie(collab_data, labels=labels, autopct='%1.1f%%', startangle=90)
            ax5.set_title('Collaboration', fontweight='bold')
        
        # 6. Language distribution (bottom row, center)
        ax6 = fig.add_subplot(gs[2, 1])
        lang_dist = stats.get('language_distribution', {})
        if lang_dist:
            sorted_langs = sorted(lang_dist.items(), key=lambda x: x[1], reverse=True)[:8]
            languages, counts = zip(*sorted_langs)
            
            bars = ax6.bar(range(len(languages)), counts, color='orange', alpha=0.7)
            ax6.set_xticks(range(len(languages)))
            ax6.set_xticklabels(languages, rotation=45, fontsize=8)
            ax6.set_title('Languages', fontweight='bold')
            ax6.set_ylabel('Publications')
        
        # 7. Summary statistics (bottom row, right)
        ax7 = fig.add_subplot(gs[2, 2])
        ax7.axis('off')
        
        summary_text = f"""
        SUMMARY STATISTICS
        
        Total Publications: {stats['total_publications']:,}
        Unique Authors: {stats['unique_authors']:,}
        Date Range: {stats['date_range']['earliest']}-{stats['date_range']['latest']}
        
        With ISBN: {stats['publications_with_isbn']:,}
        With URL: {stats['publications_with_url']:,}
        
        Collaboration Rate: {collab_stats.get('collaboration_rate', 0)*100:.1f}%
        Avg Authors/Pub: {collab_stats.get('avg_authors_per_pub', 0):.1f}
        """
        
        ax7.text(0.1, 0.9, summary_text, transform=ax7.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        # Add main title
        fig.suptitle('DNB Publication Analysis Dashboard', fontsize=20, fontweight='bold', y=0.95)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_database_source_chart(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a chart showing publication distribution by database source.
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        if not self.analyzer:
            raise ValueError("Analyzer instance required")
        
        stats = self.analyzer.get_basic_statistics()
        db_sources = stats.get('database_source_distribution', {})
        
        if not db_sources:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No database source data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title('Database Source Distribution')
            return fig
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Pie chart
        labels = list(db_sources.keys())
        sizes = list(db_sources.values())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'][:len(labels)]
        
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors,
                                          explode=[0.05] * len(labels))
        ax1.set_title('Publication Sources', fontweight='bold', fontsize=14)
        
        # Beautify pie chart text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        # Bar chart
        bars = ax2.bar(range(len(labels)), sizes, color=colors, alpha=0.7)
        ax2.set_xticks(range(len(labels)))
        ax2.set_xticklabels(labels)
        ax2.set_ylabel('Number of Publications')
        ax2.set_title('Publication Count by Database', fontweight='bold', fontsize=14)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # Add summary text
        total_pubs = sum(sizes)
        summary_text = f"Total Publications: {total_pubs:,}\n"
        if len(db_sources) > 1:
            summary_text += "Multi-Database Search Results"
        else:
            summary_text += f"Single Database: {list(db_sources.keys())[0].upper()}"
        
        fig.suptitle(summary_text, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig

    def save_all_charts(self, output_dir: str, prefix: str = "dnb_analysis") -> List[str]:
        """
        Save all individual charts to files.
        
        Args:
            output_dir: Directory to save charts
            prefix: Prefix for filenames
            
        Returns:
            List of saved file paths
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saved_files = []
        
        # Timeline chart
        try:
            fig = self.create_publication_timeline()
            path = os.path.join(output_dir, f"{prefix}_timeline.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating timeline chart: {e}")
        
        # Author productivity
        try:
            fig = self.create_author_productivity_chart()
            path = os.path.join(output_dir, f"{prefix}_authors.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating author chart: {e}")
        
        # Subject distribution
        try:
            fig = self.create_subject_wordcloud_chart()
            path = os.path.join(output_dir, f"{prefix}_subjects.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating subject chart: {e}")
        
        # Publication types
        try:
            fig = self.create_publication_type_pie_chart()
            path = os.path.join(output_dir, f"{prefix}_types.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating types chart: {e}")
        
        # Collaboration analysis
        try:
            fig = self.create_collaboration_analysis()
            path = os.path.join(output_dir, f"{prefix}_collaboration.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating collaboration chart: {e}")
        
        # Comprehensive dashboard
        try:
            fig = self.create_comprehensive_dashboard()
            path = os.path.join(output_dir, f"{prefix}_dashboard.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating dashboard: {e}")
        
        # Database source distribution
        try:
            fig = self.create_database_source_chart()
            path = os.path.join(output_dir, f"{prefix}_database_sources.png")
            fig.savefig(path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            saved_files.append(path)
        except Exception as e:
            print(f"Error creating database source chart: {e}")

        return saved_files
