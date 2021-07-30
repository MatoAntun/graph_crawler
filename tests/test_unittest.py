from unittest.loader import findTestCases
import pytest
import unittest
import mgclient
import logging
import os
import sys
from main import DepthCrawler
from unittest import mock
from unittest import TestCase, main, mock

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(
    os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


logger = logging.getLogger('scrap_test_logger')

class TestMockResponse(unittest.TestCase):

    @mock.patch("main.requests.get")
    def test_call_request_webpage(self, mock_get):
        """ Mocking class for successful request"""

        my_mock_response = mock.Mock(status_code=200)
        my_mock_response.json.return_value = {
            ""
        }
        mock_get.return_value = my_mock_response
        # factory
        response = DepthCrawler().request_webpage("www.memGrof.com/existing")
        self.assertEqual(response.status_code, 200)


    @mock.patch("main.requests.get")
    def test_call_fail_request_webpage(self, mock_get):
        """ mocking class for request get failure """

        my_mock_response = mock.Mock(status_code=404)
        my_mock_response.json.return_value = {
            ""
        }
        mock_get.return_value = my_mock_response
        # factory
        response = DepthCrawler().request_webpage("www.memGrof.com/non/existing")
        self.assertEqual(response.status_code, 404)

    def test_get_url(self):
        """ Test get url """

        url = "https://www.Memgraph.com"
        get_url = DepthCrawler(url).get_url()
        assert get_url == url

    def test_check_url_correct(self):
        """ Testing url form correct response """

        url = "https://www.Memgraph.com"
        bool_check = DepthCrawler().url_check(url)
        assert bool_check == True

    def test_check_url_false(self):
        """ Checking url false form """

        url = "www.Memgraph.com"
        bool_check = DepthCrawler().url_check(url)
        assert bool_check == False

    def test__join_url_mailto(self):
        """ Testing returning noone on mailto """

        url = "mailto:someone@yoursite.com"
        url_joined = DepthCrawler()._join_url(url)
        assert url_joined is None

    def test__join_url_http(self):
        """ Testing will we join internal link without netloc to rest"""

        root_url = "https://memgraph.com/"
        url = "/download"
        url_joined = DepthCrawler(root_url)._join_url(url)
        assert url_joined == "https://memgraph.com/download"

    def test_creating_node_query(self):
        """ Testing creating node """

        root_url = "https://memgraph.com/"
        node_creation = """CREATE (u:Url {{name: '{link}'}});""".format(link=root_url)
        print(node_creation)
        assert node_creation == "CREATE (u:Url {name: 'https://memgraph.com/'});"

    def test_create_relationships_query(self):
        """ Testing relationship query"""

        url_parent = "https://memgraph.com/"
        url_child = "https://mato.com/"
        node_relationship = """
        MATCH (u:Url),(m:Url)
        WHERE u.name = '{parent}' AND m.name = '{child}'
        CREATE (u)-[r:PARENT {{ Distance: 1 }}]->(m)
        RETURN u,m,r;""".format(parent=url_parent, child=url_child)
        node_correct = "\n        MATCH (u:Url),(m:Url)\n        WHERE u.name = 'https://memgraph.com/' AND m.name = 'https://mato.com/'\n        CREATE (u)-[r:PARENT { Distance: 1 }]->(m)\n        RETURN u,m,r;"

        assert node_correct == node_relationship

    def test_check_if_relationsip_exist(self):
        """ Query string for checking if relationship exist """

        url_parent = "https://memgraph.com/"
        url_child = "https://mato.com/"
        correct_query = "\n                MATCH (u:Url)-[r:PARENT]-(m:Url)\n                WHERE u.name = 'https://memgraph.com/' AND m.name = 'https://mato.com/'\n                RETURN u.name, m.name"
        relationship_query ="""
                MATCH (u:Url)-[r:PARENT]-(m:Url)
                WHERE u.name = '{parent}' AND m.name = '{child}'
                RETURN u.name, m.name""".format(parent = url_parent, child = url_child)

        assert relationship_query == correct_query

    def test_check_if_node_exist(self):
        """ Query to check if node exists """
        node_name = "https://memgraph.com/"
        correct_query = "\n        MATCH (u:Url)\n        WHERE u.name = 'https://memgraph.com/'\n        RETURN u.name;"
        query = """
        MATCH (u:Url)
        WHERE u.name = '{node}'
        RETURN u.name;""".format(node=node_name)

        assert query == correct_query

    def test_delete_database_data(self):
        """ Query to delete database """
        query = "MATCH (n) DETACH DELETE n"
        assert query == "MATCH (n) DETACH DELETE n"

