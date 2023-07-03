"""
Riverbed Stingray Pools
"""
from .base import Resource
from pyray import exceptions

class Pools(Resource):

    def all(self):
        """
        Retrieve a list of all configured pools.
        """
        method = 'GET'
        resp, respbody = self.manager.time_request(self.manager.api_url + self.POOLS_URL, method)
        return [pool['name'] for pool in respbody['children']]

    def get(self, name):
        """
        Retrieve details for a given pool name

        :param name: A pool name
        :type name: str

        :rtype: dict
        """
        method = 'GET'
        pool_url = self.POOLS_URL + name
        resp, respbody = self.manager.time_request(self.manager.api_url + pool_url, method)
        if respbody.has_key('error_id'):
            raise exceptions.ResourceNotFound('{} does not exist'.format(name))
        return Pool(self.manager, pool_name=name, details=respbody)

    def delete(self, name):
        """
        Delete a given pool

        :param name: A pool name
        :type name: str
        """
        method = 'DELETE'
        pool_url = self.POOLS_URL + name
        resp, respbody = self.manager.time_request(self.manager.api_url + pool_url, method)
        if resp.status_code is 204:
            return True
        else:
            raise exceptions.ResourceNotFound('{} does not exist'.format(name))

class Pool(Resource):

    def __init__(self, manager, pool_name, details):
        self.manager = manager
        self.pool_name = pool_name
        self.details = details

    def _validate_node(self, node, action):
        """
        Given a node, validate if it is a valid node in the pool

        :param nodes: A node to validate
        :type nodes: str
        """
        # Validate that node is draining
        if action == 'undrain':
            if node not in self.draining_nodes:
                raise exceptions.DrainError(
                        '{} is not draining'.format(node))
        # Validate that node is active and not already draining
        if action == 'drain':
            if node not in self.nodes:
                raise exceptions.NodeNotInPool(
                        '{} is not in pool {}'.format(node, self.pool_name))
            elif node in self.draining_nodes:
                raise exceptions.DrainError(
                        '{} is already draining'.format(node))

    @property
    def draining_nodes(self):
        """
        Return a list of nodes draining
        """
        return self.details['properties']['basic']['draining']

    @property
    def nodes(self):
        """
        Return a list of nodes in the pool
        """
        return self.details['properties']['basic']['nodes']

    def drain_nodes(self, nodes=[]):
        """
        Given a list of nodes, put them in 'draining' status

        :param nodes: A list of nodes to drain
        :type nodes: list
        """
        method = 'PUT'
        pool_url = self.POOLS_URL + self.pool_name
        for node in nodes:
            self._validate_node(node, action='drain')
            self.details['properties']['basic']['draining'].append(node)

        # Send the updated config to the LB
        resp, respbody =  self.manager.time_request(self.manager.api_url + pool_url,
                                                    method,
                                                    data=self.details)
        # Validate response
        if resp.status_code is not 200:
            error = respbody['error_info']['basic']['draining']['error_text']
            raise exceptions.DrainError('Drain Error: {}'.format(error))
        else:
            return respbody

    def undrain_nodes(self, nodes=[]):
        """
        Given a list of nodes, put them in 'active' status

        :param nodes: A list of nodes to activate
        :type nodes: list
        """
        method = 'PUT'
        pool_url = self.POOLS_URL + self.pool_name
        for node in nodes:
            self._validate_node(node, action='undrain')
            self.details['properties']['basic']['draining'].remove(node)

        # Send the updated config to the LB
        return self.manager.time_request(self.manager.api_url + pool_url,
                                         method,
                                         data=self.details)

    def node_details(self):
        """
        Return all the nodes in the pool with their details.
        """
        nodes = {}
        tms_children = self.poll_all_tms()
        # Get all of our pools and nodes
        for tm in tms_children:
            per_pool_node_url = self.manager.api_url + tm['href'] + 'statistics/nodes/per_pool_node/'
            resp, respbody = self.manager.time_request(per_pool_node_url, 'GET')
            pools_to_nodes = [entry for entry in respbody['children']]

        for node in pools_to_nodes:
            if self.pool_name in node['href']:
                node_detail_url = self.manager.api_url + node['href']
                resp, respbody = self.manager.time_request(node_detail_url, 'GET')
                nodes[node['name']] = respbody
        return nodes


