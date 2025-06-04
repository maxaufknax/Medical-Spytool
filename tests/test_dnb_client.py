"""
Unit tests for DNB API client functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET
from dnb_spytool.api.dnb_client import DNBClient
from dnb_spytool.api.parser import MARCXMLParser
import requests
import pytest


class TestDNBClient:
    
    @pytest.fixture
    def dnb_client(self):
        return DNBClient()
    
    @pytest.fixture
    def mock_xml_response(self):
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
            <srw:numberOfRecords>150</srw:numberOfRecords>
            <srw:records>
                <srw:record>
                    <srw:recordData>
                        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" 
                                   xmlns:dc="http://purl.org/dc/elements/1.1/">
                            <dc:title>Test Publication 1</dc:title>
                            <dc:creator>Test Author</dc:creator>
                            <dc:date>2023</dc:date>
                            <dc:publisher>Test Publisher</dc:publisher>
                        </oai_dc:dc>
                    </srw:recordData>
                </srw:record>
                <srw:record>
                    <srw:recordData>
                        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" 
                                   xmlns:dc="http://purl.org/dc/elements/1.1/">
                            <dc:title>Test Publication 2</dc:title>
                            <dc:creator>Test Author</dc:creator>
                            <dc:date>2022</dc:date>
                            <dc:publisher>Another Publisher</dc:publisher>
                        </oai_dc:dc>
                    </srw:recordData>
                </srw:record>
            </srw:records>
        </srw:searchRetrieveResponse>'''

    def test_search_by_author_success(self, dnb_client, mock_xml_response):
        with patch.object(dnb_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = mock_xml_response.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = dnb_client.search_by_author("Test Author", 1, 10)
            
            assert result['total_records'] == 150
            assert len(result['records']) == 2
            assert result['records'][0]['title'] == 'Test Publication 1'
            assert result['records'][0]['source'] == 'DNB'

    def test_fetch_publications_pagination(self, dnb_client):
        """Test pagination logic with multiple pages"""
        
        def mock_search_by_author(author, start, max_records):
            if start == 1:
                return {
                    'total_records': 250,
                    'records': [{'title': f'Publication {i}', 'source': 'DNB'} for i in range(1, 101)],
                    'start_record': 1,
                    'records_returned': 100
                }
            elif start == 101:
                return {
                    'total_records': 250,
                    'records': [{'title': f'Publication {i}', 'source': 'DNB'} for i in range(101, 201)],
                    'start_record': 101,
                    'records_returned': 100
                }
            elif start == 201:
                return {
                    'total_records': 250,
                    'records': [{'title': f'Publication {i}', 'source': 'DNB'} for i in range(201, 251)],
                    'start_record': 201,
                    'records_returned': 50
                }
            else:
                return {'total_records': 250, 'records': [], 'start_record': start, 'records_returned': 0}
        
        with patch.object(dnb_client, 'search_by_author', side_effect=mock_search_by_author):
            # Test retrieving all results
            results = dnb_client.search_publications("Test Author")
            assert len(results) == 250
            
            # Test with limit
            results_limited = dnb_client.search_publications("Test Author", max_results=150)
            assert len(results_limited) == 150

    def test_search_publications_no_results(self, dnb_client):
        """Test behavior when no publications are found"""
        
        def mock_search_by_author(author, start, max_records):
            return {
                'total_records': 0,
                'records': [],
                'start_record': 1,
                'records_returned': 0
            }
        
        with patch.object(dnb_client, 'search_by_author', side_effect=mock_search_by_author):
            results = dnb_client.search_publications("Nonexistent Author")
            assert len(results) == 0

    def test_search_publications_network_error(self, dnb_client):
        """Test handling of network errors"""
        
        with patch.object(dnb_client, 'search_by_author', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                dnb_client.search_publications("Test Author")

    def test_search_with_special_characters(self, dnb_client, mock_xml_response):
        """Test search with special characters in author name"""
        
        with patch.object(dnb_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.content = mock_xml_response.encode('utf-8')
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Test with umlaut
            result = dnb_client.search_by_author("Müller", 1, 10)
            assert result is not None
            
            # Test with hyphen
            result = dnb_client.search_by_author("Smith-Jones", 1, 10)
            assert result is not None

    def test_minimal_api_calls(self, dnb_client):
        """Test that minimal number of API calls are made"""
        
        call_count = 0
        
        def mock_search_by_author(author, start, max_records):
            nonlocal call_count
            call_count += 1
            
            if start == 1:
                return {
                    'total_records': 50,
                    'records': [{'title': f'Publication {i}', 'source': 'DNB'} for i in range(1, 51)],
                    'start_record': 1,
                    'records_returned': 50
                }
            else:
                return {'total_records': 50, 'records': [], 'start_record': start, 'records_returned': 0}
        
        with patch.object(dnb_client, 'search_by_author', side_effect=mock_search_by_author):
            results = dnb_client.search_publications("Test Author")
            
            # Should only make 1 call since all results fit in first page
            assert call_count == 1
            assert len(results) == 50

    def test_connection_test(self, dnb_client):
        """Test the connection test functionality"""
        
        with patch.object(dnb_client.session, 'get') as mock_get:
            # Test successful connection
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            assert dnb_client.test_connection() == True
            
            # Test failed connection
            mock_get.side_effect = Exception("Connection failed")
            assert dnb_client.test_connection() == False
