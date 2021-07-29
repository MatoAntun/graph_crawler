from typing import List
from bs4 import BeautifulSoup
import requests
from app.exceptions import WebsiteNotFoundError, ShortestPathNotFoundError
import logging
from urllib.parse import urlparse
from urllib.request import urljoin
import sys
import os
import mgclient

logger = logging.getLogger('scrap_logger')

connection = mgclient.connect(host='127.0.0.1', port=7687)
cursor = connection.cursor()

sys.tracebacklimit = 0

PAST_DEPTH_LINKS = []
DEPTH_COUNTER = 0
CURRENT_DEPTH_LINKS = []
CHECKED_URLS = set() # could be same as created nodes
CREATED_NODES = set()

class Parser:
    """ Parse for webpage """

    def __init__(self, url=None, depth=2) -> None:
        self.url = url
        self.depth = depth

    def request_webpage(self,current_url:str):
        """ Request web page data """
        requested_url = None
        try:
            requested_url = requests.get(current_url)
            if requested_url.status_code == 404 and self.url == current_url:
                raise WebsiteNotFoundError(f"{current_url}")

        except requests.exceptions.ConnectionError as ex:
            logger.error(str(ex))
            if self.url == current_url:
                os._exit(0)

        return requested_url

    # should check internal, external, and shortened ...
    def depth_search(self) -> None:
        try:
            global DEPTH_COUNTER,PAST_DEPTH_LINKS, CURRENT_DEPTH_LINKS
            while DEPTH_COUNTER < self.depth:
                if DEPTH_COUNTER == 0:
                    DatabaseManipulation().create_node(self.url)
                    CHECKED_URLS.add(self.url)
                    self._find_links(self.url)
                else:
                    for temp_url in PAST_DEPTH_LINKS:
                        if temp_url not in CHECKED_URLS:
                            self._find_links(temp_url)
                            CHECKED_URLS.add(temp_url)
                DEPTH_COUNTER += 1
                PAST_DEPTH_LINKS = CURRENT_DEPTH_LINKS
                CURRENT_DEPTH_LINKS = []

        except (requests.ConnectionError, WebsiteNotFoundError) as ex:
            logger.error(str(ex))
            raise ex
        except Exception as ex:
            logger.error(str(ex))
            raise ex

    def _find_links(self, temp_url : str) -> None:
        requested_page = self.request_webpage(temp_url)
        if requested_page is not None:
            soup = BeautifulSoup(requested_page.content, 'html.parser', from_encoding="utf-8")
            for link in soup.find_all("a", href=True):
                current_url = self._join_url(link.attrs['href'])
                global CURRENT_DEPTH_LINKS
                if current_url is not None:
                    DatabaseManipulation().create_node(current_url)
                    DatabaseManipulation().create_relationships(temp_url, current_url)
                    CURRENT_DEPTH_LINKS.append(current_url)

    def get_url(self):
        return self.url

    def url_check(self, url : str) -> bool:
        min_attr = ('scheme' , 'netloc')
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                return True
            else:
                return False
        except:
            return False

    # Right now simple check make complex solution later
    def _join_url(self, link : str) -> str:
        if link.startswith('mailto'):
            return None

        elif not link.startswith('http'):
            # Root should be only for v1 later change to current_url
            link = urljoin(self.url, link)

        return link

class DatabaseManipulation:
    """ Parse for webpage """
    # we could solve it with creating path https://docs.memgraph.com/cypher-manual/clauses/create/
    def create_node(self, url : str) -> None:
        global CREATED_NODES
        try:
            if url not in CREATED_NODES:
                node_creation = """CREATE (u:Url {{name: '{link}'}});""".format(link=url)
                cursor.execute(node_creation)
                CREATED_NODES.add(url)
            connection.commit()

        except Exception as ex:
            logger.error(str(ex))
            raise ex

    def create_relationships(self, url_parent : str, url_child : str) -> None:
        try:
            if url_child in CREATED_NODES and self.check_if_relationsip_exist(url_parent, url_child) is None:
                node_relationship = """
                MATCH (u:Url),(m:Url)
                WHERE u.name = '{parent}' AND m.name = '{child}'
                CREATE (u)-[r:PARENT {{ Distance: 1 }}]->(m)
                RETURN u,m,r;""".format(parent=url_parent, child=url_child)

                cursor.execute(node_relationship)

            connection.commit()

        except Exception as ex:
            logger.error(str(ex))

    def check_if_relationsip_exist(self,url_parent,url_child):
        relationship_query ="""
        MATCH (u:Url)-[r:PARENT]-(m:Url)
        WHERE u.name = '{parent}' AND m.name = '{child}'
        RETURN u.name, m.name""".format(parent = url_parent, child = url_child)

        cursor.execute(relationship_query)

        return cursor.fetchone()


    def check_if_node_exist(self, node_name:str) -> None:
        query = """
        MATCH (u:Url)
        WHERE u.name = '{node}'
        RETURN u.name;""".format(node=node_name)

        cursor.execute(query)

        node_exist = cursor.fetchone()

        return node_exist

    def find_shortest_path(self, parent_url : str, url_child : str ) -> None:

        if self.check_if_node_exist(parent_url) is None:
            raise WebsiteNotFoundError(f"{parent_url}")

        if self.check_if_node_exist(url_child) is None:
            raise WebsiteNotFoundError(f"{url_child}")

        shortest_path_query = """
        MATCH p = (:Url {{name: '{parent}'}})
        -[:PARENT * wShortest (e, v | e.Distance) total_distance]->
        (:Url {{name: '{child}'}})
        RETURN nodes(p) AS urls,total_distance;""".format(
            parent=parent_url, child=url_child
            )

        cursor.execute(shortest_path_query)

        shortest_path = cursor.fetchone()

        if shortest_path is None:
            raise ShortestPathNotFoundError(f"Shortest path for {parent_url} and {url_child} not found")

        return shortest_path

    def delete_existing_database(self) -> None:
        try:
            query = "MATCH (n) DETACH DELETE n"
            cursor.execute(query)
            connection.commit()

        except Exception as ex:
            logger.error(str(ex))
            raise ex

def parse_input_arguments(sys_args : List):
    if len(sys_args) == 3:
        if str(sys_args[1]) == "network":
            url = sys_args[2]
            if "--depth" not in sys_args:
                DatabaseManipulation().delete_existing_database()
                Parser(url = url).depth_search()
                logger.info("Finished")
    elif len(sys_args) == 5:
        if str(sys_args[1]) == "network":
            url = sys_args[2]
            if "--depth" in sys_args:
                DatabaseManipulation().delete_existing_database()
                Parser(url=url, depth=int(sys_args[4])).depth_search()
                logger.info("Finished")
    elif sys_args[1] == "path" and len(sys_args) == 4:
        start_url = sys_args[2]
        end_url = sys_args[3]
        shortest = DatabaseManipulation().find_shortest_path(start_url,end_url)
        print(f"Shortest Path: {int(shortest[1])} clicks")
        for depth_counter,url in enumerate(shortest[0]):
            url_parsing = str(url)[16:][:-3]
            print(f"{depth_counter} - {url_parsing}")
    else:
        logger.error("Problems with given command. Check if it is valid")
        os._exit(0)

if __name__ == "__main__":
    try:
          parse_input_arguments(sys.argv)
    except KeyboardInterrupt:
        print('Interrupted')
        os._exit(0)
