import SimpleHTTPServer
import BaseHTTPServer
from json import dumps


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        json_dict = parse_id(self.translate_path(path=self.path))
        if json_dict == {}:
            self.send_response((400, "Bad Request: File ID does not exist"))
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        json = dumps(json_dict)
        self.wfile.write(json)


def run():

    server_address = ('localhost', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, ServerHandler)
    sa = httpd.socket.getsockname()
    httpd.serve_forever()


def parse_id(path):
    path_split = path.split('/')
    id = path_split[len(path_split) - 1]
    if id == "FI250134":
        return {'objectId': 'a5a6d87b-e599-528b-aea0-73f5084205d5', 'fileCopies': [{'repoCode': 'collaboratory'}]}
    elif id == "FI99990" or id == "FI99996" or id == "FI99994":
        return {"dataBundle": {"dataBundleId": "78388918-f748-4bc0-8d07-28fb83840045"},
                'fileCopies': [{'repoCode': 'cghub'}]}
    elif id == "FIEGAID":
        return {"dataBundle": {"dataBundleId": "EGAF00000112559"},
                'fileCopies': [{'repoCode': 'ega'}]}
    elif id == "FIGDCID":
        return {"dataBundle": {"dataBundleId": "f483ad78-b092-4d10-9afb-eccacec9d9dc"},
                'fileCopies': [{'repoCode': 'gdc'}]}
    else:
        return {}


if __name__ == '__main__':
    run()
