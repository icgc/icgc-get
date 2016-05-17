import SimpleHTTPServer
import BaseHTTPServer
from json import dumps, load
import re
import os


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        requestline = self.requestline
        json_dict = parse_id(requestline)
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
    httpd.serve_forever()


def parse_id(request):
    manifest = re.findall(r'/manifests', request)
    ids = re.findall(r'FI\d*', request)
    uuids = re.findall(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', request)
    access_check = re.findall(r'/settings/tokens', request)
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    stub_file = open(path + "/fixtures/stub_returns.json")
    stub = load(stub_file)
    if manifest:
        return stub["download"][uuids[0]]
    elif access_check:
        return {"scope": ["aws.download", "collab.download"]}
    else:
        resp = {"hits": [], "pagination": {"pages": 1, "page": 1}}
        for id in ids:
            resp["hits"].append(stub["status"][id])
        return resp


if __name__ == '__main__':
    run()
