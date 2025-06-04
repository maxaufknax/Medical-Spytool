"""
Unit tests for MARCXML parser functionality.
"""

import unittest
import xml.etree.ElementTree as ET
from dnb_spytool.api.parser import MARCXMLParser


class TestMARCXMLParser(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.parser = MARCXMLParser()
        
    def test_extract_title_simple(self):
        """Test title extraction from simple MARC record."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="245" ind1="1" ind2="0">
                <subfield code="a">Der Zauberberg</subfield>
                <subfield code="c">Thomas Mann</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        title = self.parser._extract_title(record)
        self.assertEqual(title, "Der Zauberberg")
        
    def test_extract_title_with_subtitle(self):
        """Test title extraction with subtitle."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="245" ind1="1" ind2="0">
                <subfield code="a">Der Zauberberg :</subfield>
                <subfield code="b">Roman</subfield>
                <subfield code="c">Thomas Mann</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        title = self.parser._extract_title(record)
        self.assertEqual(title, "Der Zauberberg : Roman")
        
    def test_extract_title_no_title_field(self):
        """Test title extraction when no title field exists."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="100" ind1="1" ind2=" ">
                <subfield code="a">Mann, Thomas</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        title = self.parser._extract_title(record)
        self.assertEqual(title, "Unknown Title")
        
    def test_extract_authors_single(self):
        """Test extraction of single author."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="100" ind1="1" ind2=" ">
                <subfield code="a">Mann, Thomas</subfield>
                <subfield code="d">1875-1955</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        authors = self.parser._extract_authors(record)
        self.assertEqual(authors, ["Mann, Thomas"])
        
    def test_extract_authors_multiple(self):
        """Test extraction of multiple authors."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="100" ind1="1" ind2=" ">
                <subfield code="a">Mann, Thomas</subfield>
            </datafield>
            <datafield tag="700" ind1="1" ind2=" ">
                <subfield code="a">Zweig, Stefan</subfield>
            </datafield>
            <datafield tag="700" ind1="1" ind2=" ">
                <subfield code="a">Kafka, Franz</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        authors = self.parser._extract_authors(record)
        expected = ["Mann, Thomas", "Zweig, Stefan", "Kafka, Franz"]
        self.assertEqual(authors, expected)
        
    def test_extract_authors_no_authors(self):
        """Test extraction when no authors are present."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="245" ind1="1" ind2="0">
                <subfield code="a">Some Title</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        authors = self.parser._extract_authors(record)
        self.assertEqual(authors, ["Unknown Author"])
        
    def test_extract_publication_year(self):
        """Test publication year extraction."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="c">1924</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        year = self.parser._extract_publication_year(record)
        self.assertEqual(year, 1924)
        
    def test_extract_publication_year_complex(self):
        """Test publication year extraction from complex date."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="c">[1924]</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        year = self.parser._extract_publication_year(record)
        self.assertEqual(year, 1924)
        
    def test_extract_publication_year_range(self):
        """Test publication year extraction from date range."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="c">1920-1925</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        year = self.parser._extract_publication_year(record)
        self.assertEqual(year, 1920)
        
    def test_extract_publication_year_no_year(self):
        """Test publication year extraction when no year is present."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="245" ind1="1" ind2="0">
                <subfield code="a">Some Title</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        year = self.parser._extract_publication_year(record)
        self.assertIsNone(year)
        
    def test_extract_publisher(self):
        """Test publisher extraction."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="260" ind1=" " ind2=" ">
                <subfield code="a">Berlin :</subfield>
                <subfield code="b">S. Fischer,</subfield>
                <subfield code="c">1924</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        publisher = self.parser._extract_publisher(record)
        self.assertEqual(publisher, "S. Fischer")
        
    def test_extract_isbn(self):
        """Test ISBN extraction."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="020" ind1=" " ind2=" ">
                <subfield code="a">9783100481009</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        isbn = self.parser._extract_isbn(record)
        self.assertEqual(isbn, "9783100481009")
        
    def test_extract_isbn_with_qualifier(self):
        """Test ISBN extraction with qualifier."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="020" ind1=" " ind2=" ">
                <subfield code="a">9783100481009 (hardcover)</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        isbn = self.parser._extract_isbn(record)
        self.assertEqual(isbn, "9783100481009")
        
    def test_extract_subjects(self):
        """Test subjects extraction."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="650" ind1=" " ind2="4">
                <subfield code="a">German literature</subfield>
            </datafield>
            <datafield tag="650" ind1=" " ind2="4">
                <subfield code="a">Fiction</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        subjects = self.parser._extract_subjects(record)
        expected = ["German literature", "Fiction"]
        self.assertEqual(subjects, expected)
        
    def test_extract_language(self):
        """Test language extraction."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <controlfield tag="008">750428s1924    gw            000 1 ger d</controlfield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        language = self.parser._extract_language(record)
        self.assertEqual(language, "ger")
        
    def test_extract_language_from_041(self):
        """Test language extraction from 041 field."""
        record_xml = '''
        <record xmlns="http://www.loc.gov/MARC21/slim">
            <datafield tag="041" ind1="0" ind2=" ">
                <subfield code="a">ger</subfield>
            </datafield>
        </record>'''
        
        record = ET.fromstring(record_xml)
        language = self.parser._extract_language(record)
        self.assertEqual(language, "ger")
        
    def test_parse_publications_complete(self):
        """Test complete publication parsing."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
            <srw:records>
                <srw:record>
                    <srw:recordData>
                        <record xmlns="http://www.loc.gov/MARC21/slim">
                            <controlfield tag="008">750428s1924    gw            000 1 ger d</controlfield>
                            <datafield tag="020" ind1=" " ind2=" ">
                                <subfield code="a">9783100481009</subfield>
                            </datafield>
                            <datafield tag="100" ind1="1" ind2=" ">
                                <subfield code="a">Mann, Thomas</subfield>
                                <subfield code="d">1875-1955</subfield>
                            </datafield>
                            <datafield tag="245" ind1="1" ind2="0">
                                <subfield code="a">Der Zauberberg</subfield>
                                <subfield code="c">Thomas Mann</subfield>
                            </datafield>
                            <datafield tag="260" ind1=" " ind2=" ">
                                <subfield code="a">Berlin :</subfield>
                                <subfield code="b">S. Fischer,</subfield>
                                <subfield code="c">1924</subfield>
                            </datafield>
                            <datafield tag="650" ind1=" " ind2="4">
                                <subfield code="a">German literature</subfield>
                            </datafield>
                        </record>
                    </srw:recordData>
                </srw:record>
            </srw:records>
        </srw:searchRetrieveResponse>'''
        
        publications = self.parser.parse_publications(xml_content)
        
        self.assertEqual(len(publications), 1)
        pub = publications[0]
        
        self.assertEqual(pub['title'], "Der Zauberberg")
        self.assertEqual(pub['authors'], ["Mann, Thomas"])
        self.assertEqual(pub['publication_year'], 1924)
        self.assertEqual(pub['publisher'], "S. Fischer")
        self.assertEqual(pub['isbn'], "9783100481009")
        self.assertEqual(pub['subjects'], ["German literature"])
        self.assertEqual(pub['language'], "ger")
        
    def test_parse_publications_empty_response(self):
        """Test parsing empty response."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
            <srw:numberOfRecords>0</srw:numberOfRecords>
        </srw:searchRetrieveResponse>'''
        
        publications = self.parser.parse_publications(xml_content)
        self.assertEqual(len(publications), 0)
        
    def test_parse_publications_invalid_xml(self):
        """Test parsing invalid XML."""
        invalid_xml = "This is not XML"
        
        with self.assertRaises(ET.ParseError):
            self.parser.parse_publications(invalid_xml)


if __name__ == '__main__':
    unittest.main()
