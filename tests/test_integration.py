from unittest.loader import findTestCases
from attr import s
import pytest
import unittest
import mgclient
import logging
import os
import sys
from bs4 import BeautifulSoup
from main import DepthCrawler, DatabaseManipulation
from unittest import mock
from app.exceptions import ShortestPathNotFoundError, WebsiteNotFoundError
from unittest import TestCase, main, mock

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(
    os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


logger = logging.getLogger('scrap_test_logger')

# should probably put it in setup
connection = mgclient.connect(host='127.0.0.1', port=7687)
cursor = connection.cursor()

class TestIntegration:
    """ Integration testing (atleast how much I manage to do)"""
    @pytest.fixture(autouse=True)
    def tearDown(self):
        """ After every test cleaning database """
        DatabaseManipulation().delete_database_data()

    @pytest.fixture
    def mock_data(self):
        """ Mock data for integration testing """
        with open('output1.html', 'r') as f:
            contents = f.read()

        return contents

    @pytest.fixture
    def fetch_all_from_database(self):
        """ Check len of database edges  """
        query = """MATCH (c:Url) RETURN c;"""

        cursor.execute(query)

        return cursor.fetchall()

    @pytest.fixture
    def fetch_one_from_database(self):
        """ Feetch one from database return c  """
        query = """MATCH (c:Url) RETURN c;"""

        cursor.execute(query)

        return cursor.fetchone()

    @pytest.fixture
    def fetch_one_name_from_database(self):
        """ Return name from database  """
        query = """MATCH (c:Url) RETURN c.name;"""

        cursor.execute(query)

        return cursor.fetchone()

    def test_check_relationship_exist(self):
        """ Check if relationship exist while nodes are not created"""
        url_parent = "https://memgraph.com/"
        url_child = "https://memgraph.com/child"

        assert DatabaseManipulation().check_if_relationsip_exist(url_parent, url_child) is None

    def test_creating_relationships(self):
        """ Create relationship and check if it exist"""
        url_parent = "https://memgraph.com/"
        url_child = "https://memgraph.com/child"

        DatabaseManipulation().create_node(url_parent)
        DatabaseManipulation().create_node(url_child)

        DatabaseManipulation().create_relationships(url_parent, url_child)

        assert DatabaseManipulation().check_if_relationsip_exist(url_parent, url_child) is not None

    def test_find_shortest_path(self):
        """ Simple test to check if we get correct shortest path """
        url_parent = "https://memgraph.com/path"
        url_child = "https://memgraph.com/child/path"

        DatabaseManipulation().create_node(url_parent)
        DatabaseManipulation().create_node(url_child)

        DatabaseManipulation().create_relationships(url_parent, url_child)

        assert DatabaseManipulation().find_shortest_path(url_parent, url_child)[1] == 1

    def test_find_shortest_path_website_not_found(self):
        """ Simple test to check if we get correct shortest path """
        url_parent = "https://memgraph.com/"
        url_child = "https://memgraph.com/child"

        DatabaseManipulation().create_node(url_parent)

        DatabaseManipulation().create_relationships(url_parent, url_child)

        with pytest.raises(WebsiteNotFoundError) as ex:
            AssertionError(DatabaseManipulation().find_shortest_path(url_parent, url_child)[1])


    def test_find_shortest_path_path_not_found(self):
        """ Simple test to check if we get correct shortest path """
        url_parent = "https://memgraph.com/1"
        url_child = "https://memgraph.com/child1"

        DatabaseManipulation().create_node(url_parent)
        DatabaseManipulation().create_node(url_child)

        DatabaseManipulation().create_relationships(url_parent, url_child)

        with pytest.raises(ShortestPathNotFoundError) as ex:
            AssertionError(DatabaseManipulation().find_shortest_path(url_child, url_parent)[1])

    def test_teardown(self, fetch_all_from_database):
        assert len(fetch_all_from_database) == 0