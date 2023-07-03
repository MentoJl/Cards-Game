import json
import time
import logging
import requests
from pyray import exceptions
from pyray import pools

class HTTPClient(object):
    """ Client for communicating to the Riverbed Stingray API """

    USER_AGENT = 'pyray-client'

    def __init__(self, service_url, username, password,
                 port=9070, verify_ssl=False, debug=False):
        """
        Initiate a client to query the Riverbed Stingray API.

        Default timeout is 30 seconds.

        :param service_url: Address used to contact the load balancer API
        :type service_url: str
        :param username: The username to connect to the load balancer
        :type username: str
        :param password: The password required to login as user
        :type password: str
        :param port: Port used to contact the load balancer API. Default: 9070
        :type port: str
        :param verify_ssl: Verify SSL validation. Default: False
        :type verify_ssl: bool
        """
        self.username = username
        self.password = password
        self.service_url = service_url.rstrip('/')
        self.port = port
        self.debug = debug
        self.timeout = float(30)
        self.verify_ssl = True if verify_ssl else False
        self.api_url = self.set_api_url(self.service_url, self.port)

        self.times = []  # [("item", starttime, endtime), ...]

        self._logger = logging.getLogger(__name__)
        if self.debug and not self._logger.handlers:
            ch = logging.StreamHandler()
            self._logger.addHandler(ch)
            self._logger.setLevel(logging.DEBUG)
            self._logger.propagate = True
            if hasattr(requests, 'logging'):
                rql = requests.logging.getLogger(requests.__name__)
                rql.addHandler(ch)
                rql.setLevel(logging.WARNING)

        # requests within the same session can reuse connections
        self.http = requests.Session()
        self.http.verify = self.verify_ssl
        self.logged_in = self._authenticate()

    def set_api_url(self, service_url, port):
        """
        Generate the full API url with the proper scheme and port

        :param service_url: Address used to contact the load balancer API
        :type service_url: str
        :param port: Port used to contact the load balancer API. Default: 9070
        :type port: str
        :rtype: str
        """
        if not service_url.startswith('https://'):
            self.service_url = 'https://{}'.format(service_url)
        return '{service_url}:{port}'.format(service_url=self.service_url,
                                             port=self.port)

    def _authenticate(self):
        """
        Establish a session with the API by making a simple
        GET request to /api/tm/2.0 and validate response code

        :rtype: bool
        """
        method = "GET"
        test_url = self.api_url + '/api/tm/2.0'
        self.http.auth = (self.username, self.password)

        resp, respbody = self.time_request(test_url, method)
        if resp.status_code is not 200:
            raise exceptions.AuthorizationFailure('Invalid Credentials. Unable to login')
        else:
            return True

    def http_log_req(self, method, url, kwargs):
        """
        Log the request in a curl format.

        :param method: An HTTP method to perform
        :type method: str
        :param url: A valid HTTP URL to call
        :type method: str
        :param kwargs: A list of optional keyword arguements passed
        :type kwargs: dict
        """
        if not self.debug:
            return
        # Log a CLI version of the request
        string_parts = ['curl -i']
        string_parts.append(" '%s'" % url)
        string_parts.append(' -X %s' % method)
        # Add all our header options
        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)
        # Add our request data
        if 'data' in kwargs:
            string_parts.append(" -d '%s'" % (kwargs['data']))
        self._logger.debug("\nREQ: %s\n" % "".join(string_parts))

    def http_log_resp(self, resp):
        """
        Log the request response body post ``json.dumps()``

        :param resp: A ``request`` object response
        :type resp: ``request`` object
        """
        if not self.debug:
            return
        self._logger.debug(
            "RESP: [%s] %s\nRESP BODY: %s\n",
            resp.status_code,
            resp.headers,
            resp.text)

    def get_timings(self):
        """
        Return a list of request times
        """
        return self.times

    def reset_timings(self):
        """
        Reset the list of request timings
        """
        self.times = []

    def request(self, url, method, **kwargs):
        """
        Wrapper around ``requests``. Adds the appropriate headers
        necessary for the stingray API.

        Pre-dumps data with json.dumps()
        Post-load data with json.load()
        Content-Type: 'application/json'

        Returns a tuple of the ``request`` response and the
        request body post json.loads()

        :param method: An HTTP method to perform
        :type method: str
        :param url: A valid HTTP URL to call
        :type method: str
        :param kwargs: A list of optional keyword arguements passed
        :type kwargs: dict
        :rtype: tuple
        """
        kwargs.setdefault('headers', kwargs.get('headers', {}))
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        if 'data' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['data'])

        self.http_log_req(method, url, kwargs)
        resp = self.http.request(method, url, **kwargs)
        self.http_log_resp(resp)

        if resp.text:
            try:
                body = json.loads(resp.text)
            except ValueError:
                body = None
        return resp, body

    def response_error(self, resp):
        """
        Validate the response and check for an error.

        :param resp: A ``request`` object response
        :type resp: ``request`` object
        """
        if resp.has_key('error_id'):
            return True
        else:
            return False

    def time_request(self, url, method, **kwargs):
        """
        Wrapper around self.request() that times the request
        and adds the result to self.times = []

        :param method: An HTTP method to perform
        :type method: str
        :param url: A valid HTTP URL to call
        :type method: str
        :param kwargs: A list of optional keyword arguements passed
        :type kwargs: dict
        :rtype: tuple
        """
        start_time = time.time()
        resp, body = self.request(url, method, **kwargs)
        self.times.append(("{} {}".format(method, url),
                           start_time, time.time()))
        return resp, body

    @property
    def pools(self):
        """
        Return the pool object corresponding to active configured pools
        """
        return pools.Pools(self)