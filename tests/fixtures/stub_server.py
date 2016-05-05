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
    httpd.serve_forever()


def parse_id(path):
    path_split = path.split('/')
    id = path_split[len(path_split) - 1]
    if id == "FI250134":
        return {'objectId': 'a5a6d87b-e599-528b-aea0-73f5084205d5', 'fileCopies': [{'repoCode': 'collaboratory',
                                                                                    'fileSize': 202180}]}
    elif id == "FI99990":
        return {"dataBundle": {"dataBundleId": "78388918-f748-4bc0-8d07-28fb83840045"},
                'fileCopies': [{'repoCode': 'cghub', 'fileSize': 202180}]}
    elif id == "FI99996":
        return {"dataBundle": {"dataBundleId": "79182d51-d38f-4003-82a7-1cd8c6dba21e"},
                'fileCopies': [{'repoCode': 'cghub', 'fileSize': 202180}]}
    elif id == "FI99994":
        return {"dataBundle": {"dataBundleId": "78388918-f748-4bc0-8d07-28fb83840045"},
                'fileCopies': [{'repoCode': 'cghub', 'fileSize': 202180}]}
    elif id == "FIEGAID":
        return {"dataBundle": {"dataBundleId": "EGAF00000112559"},
                'fileCopies': [{'repoCode': 'ega', 'fileSize': 202180}]}
    elif id == "FIGDCID":
        return {"dataBundle": {"dataBundleId": "f483ad78-b092-4d10-9afb-eccacec9d9dc"},
                'fileCopies': [{'repoCode': 'gdc', 'fileSize': 202180}]}
    elif id == "FIGDCID2":
        return {"dataBundle": {"dataBundleId": "2c759eb8-7ee0-43f5-a008-de4317ab8c70"},
                'fileCopies': [{'repoCode': 'gdc', 'fileSize': 202180}]}
    elif id == "FIGDCID3":
        return {"dataBundle": {"dataBundleId": "a6b2f1ff-5c71-493c-b65d-e344ed29b7bb"},
                'fileCopies': [{'repoCode': 'gdc', 'fileSize': 202180}]}
    elif id == "MAGDC":
        return [{"repo": "gdc", "fileIds": ["FIGDCID","FIGDCID2","FIGDCID3"]}]
    elif id == "MAEGA":
        return [{"repo": "ega", "fileIds": ["FIEGAID"]}]
    elif id == "MAICGC":
        return [{"repo": "collaboratory", "fileIds": ["FI250134"]}]
    elif id == "MACGHUB":
        return [{"repo": "gdc", "fileIds": ["FI99996", "FI99994", "FI99990"]}]
    else:
        return {}


if __name__ == '__main__':
    run()
