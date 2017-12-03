from abc import abstractmethod

import requests

class APIProxy(object):
    def _request(self, url, method='get', **kwargs):
        return requests.request(method, url, **kwargs)

    @abstractmethod
    def request(self, *args, **kwargs):
        pass

    @abstractmethod
    def report_api_error(self, text, *args, **kwargs):
        print('API ERROR: %s' % text)

