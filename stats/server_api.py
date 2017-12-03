from stats.api_proxy import APIProxy

class ServerAPI(APIProxy):
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 9999

    def __init__(self, api_url: str):
        self.api_url = api_url

    @staticmethod
    def _clean_result(result):
        try:
            return result.json()
        except:
            return None

    def format_url(self, method_name: str):
        return self.api_url.format(method_name=method_name)

    def request(self, method_name: str, method: str = 'post', params=None, files=None, **kwargs):
        url = self.format_url(method_name)

        read_timeout = ServerAPI.READ_TIMEOUT
        connection_timeout = ServerAPI.CONNECTION_TIMEOUT

        if params is not None:
            if 'read_timeout' in params:
                read_timeout = params['read_timeout']
                del params['read_timeout']

            if 'connection_timeout' in params:
                connection_timeout = params['connection_timeout']
                del params['connection_timeout']

        req_kwargs = dict(method=method, url=url, files=files,
                          timeout=(connection_timeout, read_timeout))

        if method.upper() == 'GET':
            req_kwargs['params'] = params
        elif method.upper() == 'POST':
            req_kwargs['json'] = params

        return self.format_result(
            self._request(**req_kwargs, **kwargs)
        )

    def format_result(self, result):
        clean_result = ServerAPI._clean_result(result)

        if clean_result is None:
            print('Warning: could not make a request to Bitrix24 API')
            return None

        if result.status_code != 200:
            # not everything ok
            text = 'Error occurred while making request to Bitrix24 API'

            if 'error' in result:
                text = str(result['error'])

            self.report_api_error(text=text)
            return text

        if 'result' in clean_result:
            return clean_result['result']

        self.report_api_error(text='No result provided by the server side')
        return None

    def get_image(self, data, file_path):

        result = self.request('createImage', 'post', params={
            'chart_data': data,
            'file_path': file_path
        })

        return result