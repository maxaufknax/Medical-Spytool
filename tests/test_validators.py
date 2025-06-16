"""
Unit tests for input validation functionality.
"""

import unittest
import tempfile
import os
from dnb_spytool.utils.validators import InputValidator


class TestInputValidator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
        
    def test_validate_author_name_valid(self):
        """Test validation of valid author names."""
        valid_names = [
            "Thomas Mann",
            "Müller, Hans",
            "García Márquez, Gabriel",
            "O'Connor, Flannery",
            "Jean-Paul Sartre",
            "李明",  # Chinese characters
            "Достоевский, Фёдор",  # Cyrillic
            "A",  # Single character
            "von Goethe, Johann Wolfgang"
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                result = self.validator.validate_author_name(name)
                self.assertTrue(result['is_valid'], f"Name '{name}' should be valid")
                self.assertEqual(result['cleaned_name'], name)
                
    def test_validate_author_name_invalid(self):
        """Test validation of invalid author names."""
        invalid_names = [
            "",  # Empty string
            "   ",  # Only whitespace
            "A" * 201,  # Too long (over 200 chars)
            "123456",  # Only numbers
            "!!!@@@",  # Only special characters
            "Author123",  # Contains numbers
        ]
        
        for name in invalid_names:
            with self.subTest(name=name):
                result = self.validator.validate_author_name(name)
                self.assertFalse(result['is_valid'], f"Name '{name}' should be invalid")
                self.assertIn('error', result)
                
    def test_validate_author_name_with_whitespace(self):
        """Test validation handles whitespace correctly."""
        name_with_whitespace = "  Thomas Mann  "
        result = self.validator.validate_author_name(name_with_whitespace)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['cleaned_name'], "Thomas Mann")
        
    def test_validate_file_path_valid_for_writing(self):
        """Test validation of valid file paths for writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_paths = [
                os.path.join(temp_dir, "test.csv"),
                os.path.join(temp_dir, "results.json"),
                os.path.join(temp_dir, "data.xlsx"),
                os.path.join(temp_dir, "report.pdf"),
                os.path.join(temp_dir, "output.html"),
            ]
            
            for path in valid_paths:
                with self.subTest(path=path):
                    result = self.validator.validate_file_path(path, check_exists=False)
                    self.assertTrue(result['is_valid'], f"Path '{path}' should be valid")
                    
    def test_validate_file_path_invalid_extension(self):
        """Test validation of file paths with invalid extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_paths = [
                os.path.join(temp_dir, "test.txt"),
                os.path.join(temp_dir, "data.doc"),
                os.path.join(temp_dir, "output.xyz"),
                os.path.join(temp_dir, "file"),  # No extension
            ]
            
            for path in invalid_paths:
                with self.subTest(path=path):
                    result = self.validator.validate_file_path(path, check_exists=False)
                    self.assertFalse(result['is_valid'], f"Path '{path}' should be invalid")
                    
    def test_validate_file_path_directory_not_exists(self):
        """Test validation when parent directory doesn't exist."""
        non_existent_path = "/non/existent/directory/file.csv"
        result = self.validator.validate_file_path(non_existent_path, check_exists=False)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('error', result)
        
    def test_validate_file_path_existing_file(self):
        """Test validation of existing files."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Test with check_exists=True (should pass for existing file)
            result = self.validator.validate_file_path(temp_path, check_exists=True)
            self.assertTrue(result['is_valid'])
            
            # Test with check_exists=False (should also pass)
            result = self.validator.validate_file_path(temp_path, check_exists=False)
            self.assertTrue(result['is_valid'])
            
        finally:
            os.unlink(temp_path)
            
    def test_validate_file_path_non_existing_with_check(self):
        """Test validation of non-existing file when check_exists=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_file = os.path.join(temp_dir, "non_existent.csv")
            result = self.validator.validate_file_path(non_existent_file, check_exists=True)
            
            self.assertFalse(result['is_valid'])
            self.assertIn('error', result)
            
    def test_validate_search_parameters_valid(self):
        """Test validation of valid search parameters."""
        valid_params = [
            {'max_results': 100},
            {'max_results': 1},
            {'max_results': 1000},
            {'start_year': 2000},
            {'end_year': 2023},
            {'start_year': 1900, 'end_year': 2023},
            {'max_results': 50, 'start_year': 2010, 'end_year': 2020},
        ]
        
        for params in valid_params:
            with self.subTest(params=params):
                result = self.validator.validate_search_parameters(**params)
                self.assertTrue(result['is_valid'], f"Params {params} should be valid")
                
    def test_validate_search_parameters_invalid_max_results(self):
        """Test validation of invalid max_results values."""
        invalid_values = [0, -1, 10001, 'invalid', None]
        
        for value in invalid_values:
            with self.subTest(value=value):
                result = self.validator.validate_search_parameters(max_results=value)
                self.assertFalse(result['is_valid'], f"max_results={value} should be invalid")
                
    def test_validate_search_parameters_invalid_years(self):
        """Test validation of invalid year values."""
        invalid_params = [
            {'start_year': 1800},  # Too early
            {'end_year': 2030},    # Future year
            {'start_year': 2020, 'end_year': 2010},  # start > end
            {'start_year': 'invalid'},  # Non-numeric
            {'end_year': None},  # None value
        ]
        
        for params in invalid_params:
            with self.subTest(params=params):
                result = self.validator.validate_search_parameters(**params)
                self.assertFalse(result['is_valid'], f"Params {params} should be invalid")
                
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        test_cases = [
            ("normal_file.csv", "normal_file.csv"),
            ("file with spaces.json", "file_with_spaces.json"),
            ("file/with\\slashes.xlsx", "file_with_slashes.xlsx"),
            ("file:with*special<>chars?.pdf", "file_with_special_chars.pdf"),
            ("file|with\"quotes'.html", "file_with_quotes.html"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.validator.sanitize_filename(input_name)
                self.assertEqual(result, expected)
                
    def test_sanitize_filename_preserve_extension(self):
        """Test that sanitization preserves file extensions."""
        result = self.validator.sanitize_filename("bad*file?.csv")
        self.assertEqual(result, "bad_file.csv")
        self.assertTrue(result.endswith('.csv'))
        
    def test_sanitize_filename_long_names(self):
        """Test sanitization of very long filenames."""
        long_name = "a" * 300 + ".csv"
        result = self.validator.sanitize_filename(long_name)
        
        # Should be truncated but keep extension
        self.assertTrue(len(result) <= 255)
        self.assertTrue(result.endswith('.csv'))
        
    def test_validate_export_format_valid(self):
        """Test validation of valid export formats."""
        valid_formats = ['csv', 'json', 'xlsx', 'pdf', 'html']
        
        for format_type in valid_formats:
            with self.subTest(format_type=format_type):
                result = self.validator.validate_export_format(format_type)
                self.assertTrue(result['is_valid'])
                
    def test_validate_export_format_invalid(self):
        """Test validation of invalid export formats."""
        invalid_formats = ['txt', 'doc', 'xyz', '', None, 123]
        
        for format_type in invalid_formats:
            with self.subTest(format_type=format_type):
                result = self.validator.validate_export_format(format_type)
                self.assertFalse(result['is_valid'])
                
    def test_validate_export_format_case_insensitive(self):
        """Test that export format validation is case insensitive."""
        formats_to_test = ['CSV', 'Json', 'XLSX', 'PDF', 'Html']
        
        for format_type in formats_to_test:
            with self.subTest(format_type=format_type):
                result = self.validator.validate_export_format(format_type)
                self.assertTrue(result['is_valid'])
                
    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = self.validator.get_supported_formats()
        expected = ['csv', 'json', 'xlsx', 'pdf', 'html']
        
        self.assertEqual(sorted(formats), sorted(expected))
        
    def test_validation_result_structure(self):
        """Test that validation results have consistent structure."""
        # Test valid case
        result = self.validator.validate_author_name("Valid Author")
        self.assertIn('is_valid', result)
        self.assertIn('cleaned_name', result)
        self.assertTrue(result['is_valid'])
        
        # Test invalid case
        result = self.validator.validate_author_name("")
        self.assertIn('is_valid', result)
        self.assertIn('error', result)
        self.assertFalse(result['is_valid'])


if __name__ == '__main__':
    unittest.main()
