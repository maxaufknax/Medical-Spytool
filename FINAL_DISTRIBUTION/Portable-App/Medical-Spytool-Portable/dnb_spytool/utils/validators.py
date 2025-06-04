"""
Input validation utilities for the DNB Spytool application.
"""

import re
from typing import List, Optional, Dict, Any
import os
from urllib.parse import urlparse


class InputValidator:
    """Validates user inputs for the DNB Spytool application."""
    
    def __init__(self):
        """Initialize the validator with common patterns."""
        # Common name patterns
        self.name_pattern = re.compile(r'^[a-zA-ZäöüÄÖÜß\s\-\.,\']+$')
        self.year_pattern = re.compile(r'^\d{4}$')
          # File extension mappings
        self.format_extensions = {
            'csv': '.csv',
            'json': '.json',
            'xlsx': '.xlsx',
            'pdf': '.pdf',
            'html': '.html'
        }
    
    def validate_author_name(self, author_name: str) -> Dict[str, Any]:
        """
        Validate an author name input.
        
        Args:
            author_name: Author name to validate
            
        Returns:
            Dictionary with validation results including 'cleaned_name'
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'cleaned_name': None
        }
        
        if not author_name:
            result['errors'].append("Author name cannot be empty")
            result['error'] = "Author name cannot be empty"  # For backwards compatibility
            return result
        
        if not isinstance(author_name, str):
            result['errors'].append("Author name must be a string")
            result['error'] = "Author name must be a string"
            return result
          # Clean the input
        cleaned_name = author_name.strip()
        result['cleaned_name'] = cleaned_name
        
        if len(cleaned_name) == 0:
            result['errors'].append("Author name cannot be empty after trimming")
            result['error'] = "Author name cannot be empty after trimming"
            return result
            
        if len(cleaned_name) < 1:
            result['errors'].append("Author name must be at least 1 character long")
            result['error'] = "Author name must be at least 1 character long"
            return result
        
        if len(cleaned_name) > 200:
            result['errors'].append("Author name is too long (maximum 200 characters)")
            result['error'] = "Author name is too long (maximum 200 characters)"
            return result
        
        # Enhanced character validation - allow more Unicode characters
        # Allow letters, spaces, hyphens, periods, commas, apostrophes, and Unicode characters
        extended_pattern = re.compile(r'^[\w\s\-\.,\'äöüÄÖÜßáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛñÑçÇ\u4e00-\u9fff\u0400-\u04ff]+$', re.UNICODE)
        
        # Check for only numbers
        if re.match(r'^\d+$', cleaned_name):
            result['errors'].append("Author name cannot contain only numbers")
            result['error'] = "Author name cannot contain only numbers"
            return result
        
        # Check for only special characters
        if re.match(r'^[^\w\s]+$', cleaned_name):
            result['errors'].append("Author name cannot contain only special characters")
            result['error'] = "Author name cannot contain only special characters"
            return result        # Check for suspicious patterns - only reject pure numbers, not names with numbers
        if re.search(r'\d', cleaned_name):
            result['errors'].append("Author name cannot contain numbers")
            result['error'] = "Author name cannot contain numbers"
            return result
        
        if re.search(r'[@#$%&*!+=<>{}[\]|\\\/]', cleaned_name):
            result['errors'].append("Author name contains invalid special characters")
            result['error'] = "Author name contains invalid special characters"
            return result
        
        if re.search(r'[.,]{2,}', cleaned_name):
            result['warnings'].append("Author name contains multiple consecutive punctuation marks")
        
        if cleaned_name.lower() in ['test', 'example', 'sample', 'dummy']:
            result['warnings'].append("Author name appears to be a test value")
          # Suggestions for formatting
        if cleaned_name != cleaned_name.title():
            result['suggestions'].append(f"Consider proper capitalization: '{cleaned_name.title()}'")
        
        if '  ' in cleaned_name:
            result['suggestions'].append("Consider removing extra spaces")
            result['suggestions'].append(f"Suggested: '{re.sub(r'\s+', ' ', cleaned_name)}'")
          # Final validation - return properly cleaned name
        result['cleaned_name'] = cleaned_name
        result['is_valid'] = True
        return result
    
    def validate_author_list(self, authors: List[str]) -> Dict[str, Any]:
        """
        Validate a list of author names.
        
        Args:
            authors: List of author names to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'valid_authors': [],
            'invalid_authors': []
        }
        
        if not authors:
            result['errors'].append("Author list cannot be empty")
            return result
        
        if not isinstance(authors, list):
            result['errors'].append("Authors must be provided as a list")
            return result
        
        if len(authors) > 50:
            result['warnings'].append(f"Large number of authors ({len(authors)}). This may take a long time to process")
        
        # Validate each author
        for i, author in enumerate(authors):
            author_result = self.validate_author_name(author)
            
            if author_result['is_valid']:
                result['valid_authors'].append(author.strip())
            else:
                result['invalid_authors'].append({
                    'index': i,
                    'name': author,
                    'errors': author_result['errors']
                })
        
        # Check for duplicates
        cleaned_authors = [author.strip().lower() for author in result['valid_authors']]
        duplicates = []
        seen = set()
        
        for author in cleaned_authors:
            if author in seen:
                duplicates.append(author)
            seen.add(author)
        
        if duplicates:
            result['warnings'].append(f"Duplicate authors found: {', '.join(set(duplicates))}")
        
        # Final validation
        if result['valid_authors']:
            result['is_valid'] = True
        else:
            result['errors'].append("No valid authors found in the list")
        
        return result
    
    def validate_output_path(self, output_path: str, format_type: str) -> Dict[str, Any]:
        """
        Validate an output file path.
        
        Args:
            output_path: Output file path to validate
            format_type: Expected file format
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if not output_path:
            result['errors'].append("Output path cannot be empty")
            return result
        
        if not isinstance(output_path, str):
            result['errors'].append("Output path must be a string")
            return result
        
        # Clean the path
        output_path = output_path.strip()
        
        # Check if it's a valid path format
        try:
            # Check for invalid characters (Windows-friendly)
            # Note: On Windows, colon is valid in drive letters (C:), so we only check for colon 
            # if it's not the second character (drive letter position)
            invalid_chars = '<>"|?*'
            if any(char in output_path for char in invalid_chars):
                result['errors'].append(f"Output path contains invalid characters: {invalid_chars}")
                return result
                
            # Check for invalid colon placement (not in drive letter position)
            import platform
            if platform.system() == 'Windows':
                # On Windows, colon is only valid as second character for drive letters
                if ':' in output_path:
                    colon_positions = [i for i, char in enumerate(output_path) if char == ':']
                    for pos in colon_positions:
                        if pos != 1:  # Drive letter position is index 1 (e.g., "C:")
                            result['errors'].append("Colon character ':' is only valid in drive letters on Windows")
                            return result
            else:
                # On non-Windows systems, colon is generally invalid in filenames
                if ':' in output_path:
                    result['errors'].append("Output path contains invalid character: ':'")
                    return result
            
            # Get directory and filename
            directory = os.path.dirname(output_path)
            filename = os.path.basename(output_path)
            
            if not filename:
                result['errors'].append("Output path must include a filename")
                return result
            
            # Check directory exists or can be created
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    result['suggestions'].append(f"Directory will be created: {directory}")
                except Exception as e:
                    result['errors'].append(f"Cannot create directory {directory}: {e}")
                    return result
            
            # Check file extension
            expected_ext = self.format_extensions.get(format_type.lower())
            if expected_ext:
                if not output_path.lower().endswith(expected_ext):
                    result['warnings'].append(f"File extension doesn't match format. Expected: {expected_ext}")
                    result['suggestions'].append(f"Consider: {output_path}{expected_ext}")
            
            # Check if file already exists
            if os.path.exists(output_path):
                result['warnings'].append("File already exists and will be overwritten")
            
            # Check write permissions
            test_dir = directory if directory else os.getcwd()
            if not os.access(test_dir, os.W_OK):
                result['errors'].append(f"No write permission for directory: {test_dir}")
                return result
            
        except Exception as e:
            result['errors'].append(f"Invalid path format: {e}")
            return result
        
        result['is_valid'] = True
        return result
    
    def validate_search_parameters(self, **kwargs) -> Dict[str, Any]:
        """
        Validate search parameters.
        
        Args:
            **kwargs: Search parameters to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }        # Validate max_records/max_results
        max_records = kwargs.get('max_records') or kwargs.get('max_results')
        if max_records is not None:
            if not isinstance(max_records, int):
                try:
                    max_records = int(max_records)
                except (ValueError, TypeError):
                    result['errors'].append("max_records must be an integer")
                    return result
            
            if max_records <= 0:
                result['errors'].append("max_records must be greater than 0")
                return result
            
            if max_records > 10000:
                result['errors'].append("max_records cannot exceed 10000")
                return result
        elif 'max_results' in kwargs and kwargs['max_results'] is None:
            # Explicitly passed None is invalid
            result['errors'].append("max_records cannot be None")
            return result
            
            if max_records > 1000:
                result['warnings'].append("Large max_records value may cause long processing times")
                result['suggestions'].append("Consider using smaller batches for better performance")        # Validate year range
        start_year = kwargs.get('start_year')
        end_year = kwargs.get('end_year')
        
        # Check for explicitly passed None values
        if 'start_year' in kwargs and kwargs['start_year'] is None:
            result['errors'].append("start_year cannot be None")
            return result
            
        if 'end_year' in kwargs and kwargs['end_year'] is None:
            result['errors'].append("end_year cannot be None")
            return result
        
        if start_year is not None:
            if not self._validate_year(start_year):
                result['errors'].append("start_year must be a valid 4-digit year between 1850 and 2025")
                return result
        
        if end_year is not None:
            if not self._validate_year(end_year):
                result['errors'].append("end_year must be a valid 4-digit year between 1850 and 2025")
                return result
        
        if start_year and end_year and int(start_year) > int(end_year):
            result['errors'].append("start_year cannot be greater than end_year")
            return result        # Validate format
        format_type = kwargs.get('format', 'csv')
        if format_type not in self.format_extensions:
            result['errors'].append(f"Unsupported format: {format_type}")
            result['suggestions'].append(f"Supported formats: {', '.join(self.format_extensions.keys())}")
            return result
        
        result['is_valid'] = True
        return result
    
    def _validate_year(self, year) -> bool:
        """Validate a year value."""
        if year is None:
            return False
            
        if isinstance(year, int):
            year = str(year)
        
        if not isinstance(year, str):
            return False
        
        if not self.year_pattern.match(year):
            return False
        
        year_int = int(year)
        # Current year is 2025, so future years beyond 2025 should be invalid
        return 1850 <= year_int <= 2025
    
    def validate_export_format(self, format_type: str) -> Dict[str, Any]:
        """
        Validate an export format.
        
        Args:
            format_type: Format to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if not format_type:
            result['errors'].append("Export format cannot be empty")
            return result
        
        if not isinstance(format_type, str):
            result['errors'].append("Export format must be a string")
            return result
        
        # Case insensitive check
        format_lower = format_type.lower()
        
        if format_lower not in self.format_extensions:
            result['errors'].append(f"Unsupported format: {format_type}")
            result['suggestions'].append(f"Supported formats: {', '.join(self.format_extensions.keys())}")
            return result
        
        result['is_valid'] = True
        return result
    
    def validate_file_path(self, file_path: str, check_exists: bool = False) -> Dict[str, Any]:
        """
        Validate a file path.
        
        Args:
            file_path: File path to validate
            check_exists: Whether to check if file exists
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        if not file_path:
            result['errors'].append("File path cannot be empty")
            return result
        
        if not isinstance(file_path, str):
            result['errors'].append("File path must be a string")
            return result
        
        # Clean the path
        file_path = file_path.strip()
        
        # Check for invalid characters (Windows-friendly)
        # Note: On Windows, colon is valid in drive letters (C:), so we only check for colon 
        # if it's not the second character (drive letter position)
        invalid_chars = '<>"|?*'
        if any(char in file_path for char in invalid_chars):
            result['errors'].append(f"File path contains invalid characters: {invalid_chars}")
            return result
            
        # Check for invalid colon placement (not in drive letter position)
        import platform
        if platform.system() == 'Windows':
            # On Windows, colon is only valid as second character for drive letters
            if ':' in file_path:
                colon_positions = [i for i, char in enumerate(file_path) if char == ':']
                for pos in colon_positions:
                    if pos != 1:  # Drive letter position is index 1 (e.g., "C:")
                        result['errors'].append("Colon character ':' is only valid in drive letters on Windows")
                        return result
        else:
            # On non-Windows systems, colon is generally invalid in filenames
            if ':' in file_path:
                result['errors'].append("File path contains invalid character: ':'")
                return result
        
        # Check file extension
        filename = os.path.basename(file_path)
        if not filename:
            result['errors'].append("File path must include a filename")
            return result
          # Check if extension is supported  
        _, ext = os.path.splitext(filename)
        if not ext:  # Missing extension
            result['errors'].append("File path must have a file extension")
            result['suggestions'].append(f"Supported extensions: {', '.join(self.format_extensions.values())}")
            return result
        
        valid_extensions = list(self.format_extensions.values())
        if ext.lower() not in valid_extensions:
            result['errors'].append(f"Unsupported file extension: {ext}")
            result['suggestions'].append(f"Supported extensions: {', '.join(valid_extensions)}")
            return result
          # Check directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            result['errors'].append(f"Directory does not exist: {directory}")
            result['error'] = f"Directory does not exist: {directory}"  # Backwards compatibility
            return result
          # Check if file exists when required
        if check_exists and not os.path.exists(file_path):
            result['errors'].append(f"File does not exist: {file_path}")
            result['error'] = f"File does not exist: {file_path}"  # Backwards compatibility
            return result
        
        # Check write permissions
        test_dir = directory if directory else os.getcwd()
        if not os.access(test_dir, os.W_OK):
            result['errors'].append(f"No write permission for directory: {test_dir}")
            return result
        
        result['is_valid'] = True
        return result
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats.
        
        Returns:
            List of supported format strings
        """
        return list(self.format_extensions.keys())
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing/replacing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "output"
        
        # Split filename and extension
        name, ext = os.path.splitext(filename)
          # Remove or replace invalid characters in the name part
        invalid_chars = '<>:"|?*/\\\'`'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Replace multiple spaces and underscores with single underscore
        name = re.sub(r'[\s_]+', '_', name)
        
        # Remove leading/trailing dots, spaces, and underscores
        name = name.strip('. _')
        
        # Remove trailing question mark if present
        name = re.sub(r'\?+$', '', name)
        
        # Ensure filename is not empty
        if not name:
            name = "output"
        
        # Combine name and extension
        result = name + ext
        
        # Limit length
        if len(result) > 100:
            result = name[:95-len(ext)] + ext
        
        return result
    
    def validate_url(self, url: str) -> bool:
        """
        Validate a URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def get_validation_summary(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Get a summary of multiple validation results.
        
        Args:
            validation_results: List of validation result dictionaries
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_validations': len(validation_results),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'all_errors': [],
            'all_warnings': [],
            'all_suggestions': []
        }
        
        for result in validation_results:
            if result.get('is_valid', False):
                summary['passed'] += 1
            else:
                summary['failed'] += 1
            
            summary['all_errors'].extend(result.get('errors', []))
            summary['all_warnings'].extend(result.get('warnings', []))
            summary['all_suggestions'].extend(result.get('suggestions', []))
        
        summary['warnings'] = len(summary['all_warnings'])
        summary['success_rate'] = summary['passed'] / summary['total_validations'] if summary['total_validations'] > 0 else 0
        
        return summary
