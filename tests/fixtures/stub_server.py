import SimpleHTTPServer
import BaseHTTPServer
from json import dumps
import re


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


def parse_id(path):
    ids = re.findall(r'FI\d*', path)
    uuids = re.findall(r'\w{8,8}-\w{4,4}-\w{4,4}-\w{4,4}-\w{12,12}', path)
    if ids:
        resp = {"hits": [], "pagination": {"pages": 1}}
        if "FI250134" in ids:
            resp["hits"].append({'objectId': 'a5a6d87b-e599-528b-aea0-73f5084205d5',
                                 'fileCopies': [{'repoCode': 'collaboratory', 'fileSize': 202180}]})
        if "FI99990" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "78388918-f748-4bc0-8d07-28fb83840045"},
                                 'fileCopies': [{'repoCode': 'cghub', 'fileSize': 435700000}]})
        if "FI99996" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "79182d51-d38f-4003-82a7-1cd8c6dba21e"},
                                 'fileCopies': [{'repoCode': 'cghub', 'fileSize': 3520000000}]})
        if "FI99994" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "78388918-f748-4bc0-8d07-28fb83840045"},
                                 'fileCopies': [{'repoCode': 'cghub', 'fileSize': 97270000}]})
        if "FIEGAID" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "EGAF00000112559"},
                                 'fileCopies': [{'repoCode': 'ega', 'fileSize': 5556766}]})
        if "FIGDCID" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "f483ad78-b092-4d10-9afb-eccacec9d9dc"},
                                 'fileCopies': [{'repoCode': 'gdc', 'fileSize': 1483}]})
        if "FIGDCID2" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "2c759eb8-7ee0-43f5-a008-de4317ab8c70"},
                                 'fileCopies': [{'repoCode': 'gdc', 'fileSize': 6261580}]})
        if "FIGDCID3" in ids:
            resp["hits"].append({"dataBundle": {"dataBundleId": "a6b2f1ff-5c71-493c-b65d-e344ed29b7bb"},
                                 'fileCopies': [{'repoCode': 'gdc', 'fileSize': 1399430}]})
        return resp
    elif uuids:
        if "ed78541a-0e3a-4d89-b348-f42886442aeb" in uuids.groups():
            return {"repo": "gdc", "entities": [{"id": "FIGDCID", "size": 1483}, {"id": "FIGDCID2", "size": 6261580},
                                                {"id": "FIGDCID3", "size": 1399430}]}
        elif "4294ed2b-4d41-4967-8c5d-231027fa40c7" in uuids.groups():
            return {"repo": "ega", "entries": [{"id": "FIEGAID", "size": 5556766}]}
        elif "76260cde-ad97-4c5d-b587-4a35bf72346f" in uuids.groups():
            return {"repos": ["collaboratory"], "entries": [{"id": "FI250134", "size": 202180}]}
        elif "950f60eb-1908-4b79-9b5a-060c5a29c3ae" in uuids.groups():
            return {"repos": "cghub", "entries": [{"id": "FI99996", "size": 3520000000},
                                                  {"id": "FI99994", "size": 435700000},
                                                  {"id": "FI99990", "size": 97270000}]}
    else:
        return {}


if __name__ == '__main__':
    run()
