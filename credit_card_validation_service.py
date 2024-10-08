#!/usr/bin/env python3

# Author: Michael Schwartz
# File:   credit_card_validation_service.py
# Based on logging_server.py by Rob Judd
# A simple REST service mock for credit card authorization

"""
Very simple HTTP server in python for logging requests
Usage::
    python credit_card_validation_service.py
    Uses ports 8000 (unencrypted) and 8443 (SSL)

One way To generate a key file for the service is to use openssl:
    openssl req -new -x509 -keyout localhost.pem -out localhost.pem -days 365 -nodes

"""
import json
import logging
import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import datastore

from cc_settlement import CCSettlement
from cc_transaction import CCTransaction

# A few constants to allow easy modification
cc_validation_port = 8000
cc_validation_port_ssl = 8443
cc_content_type_error = "text/html"
cc_content_type_processor = "application/json"

class HTTPRequestHandler(BaseHTTPRequestHandler):
    """Request handling class"""


    def _set_response(self, content_type=cc_content_type_processor):
        """Sends additional headers and marks the response as ready to send the body."""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', "*")
        self.end_headers()

    def _set_error(self, code, message):
        """Sends additional headers and marks the response as ready to send the body."""
        self.send_response(code)
        self.send_header('Content-type', cc_content_type_error)
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    # pre-flight
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, HEAD, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        """
        Handles GET requests.

        GET requests are not be used for Credit Card validation.
        """
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n",
                     str(self.path), str(self.headers))
        if self.path.startswith("/hello"):
            self._set_response('text/html')
            self.wfile.write("<h3>Hello!</h3>\n".encode('utf-8'))
            return
        elif not self.path.startswith("/api/validate"):
            self._set_error(404, "<p>Invalid path "+str(self.path))
            logging.error("GET request,\nPath: %s\nHeaders:\n%s\n",
                          str(self.path), str(self.headers))
            return

        self._set_error(501, "<p>GET is not supported for /api/validate<p>")
        logging.error("GET request,\nPath: %s\nHeaders:\n%s\n",
                      str(self.path), str(self.headers))
        return

    def do_POST_store(self):
        import json
        """Dumps the current list of unsettled transactions"""
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        data_content = post_data.decode('utf-8')
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), data_content)
        self._set_response()
        verbose = False
        try:
            if isinstance(data_content, dict):
                req = data_content
            elif isinstance(data_content, str):
                req = json.loads(data_content)
                if isinstance(req,dict):
                    if "verbose" in req:
                        verbose = req["verbose"]
        except:
            pass

        if verbose:
            settlement = datastore.get_unsettled()
            self.wfile.write(json.dumps(settlement).encode())
        else:
            settlement_ids = datastore.get_unsettled_keys()
            self.wfile.write(json.dumps(settlement_ids).encode())

    def do_POST_settle(self):
        """
        Handles POST request for settlement
        Only previously approved transactions can be settled, and only once.

        """
        self._set_response()
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        data_content = post_data.decode('utf-8')
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), data_content)
        # Content is a list of transactions to settle.
        # Return a settlement object
        transaction_list = CCTransaction.json_to_list(data_content)
        logging.info("POST request: Transactions: %d\n", len(transaction_list))
        settlement = CCSettlement.settle(transaction_list)
        self.wfile.write(settlement.to_json().encode())

    def do_POST_validate(self):
        """Handle the validation request"""
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        data_content = post_data.decode('utf-8')

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), data_content)

        # Here we'll take up the data to respond with and send it back to the caller.
        cc = CCTransaction.from_json(data_content)
        if cc.validate_transaction():
            if cc.authorize_transaction():
                # Should store be restricted to approvals? Or let the store qualify them?
                datastore.store(cc.data) # <- Set the transaction in an unsettled store
        logging.info("Validation response: %s\n", cc.to_json())
        self._set_response()

        self.wfile.write(cc.to_json().encode())

    def do_POST(self):
        """
        Handles POST requests.

        A POST request is where the data for the request is embedded in the body of the request.
        It has the same format as the query string of a GET request and therefore may be
        interpretted the same way.

        In order to read the request body we have to know how much data to read, this is
        called the Content-Length. It is a required part of the HTTP standard so it may
        be relied upon to be present.
        """
        if self.path == "/api/validate":
            self.do_POST_validate()
        elif self.path == "/api/settle":
            self.do_POST_settle()
        elif self.path == "/api/store":
            self.do_POST_store()
        else:
            self._set_error(404, "<p>Invalid path "+str(self.path))
            logging.error("POST request,\nPath: %s\nHeaders:\n%s\n\n",
                          str(self.path), str(self.headers))

def run(server_class=HTTPServer, handler_class=HTTPRequestHandler,
        port=cc_validation_port, use_ssl=False):
    """
    Initialize and run the HTTPServer.

    HTTPServer is a builtin Python class that contains the basics necessary to implement
    an HTTP server. In order to use it you create an instance of the server, tell it
    what port to listen on and give it a RequestHandler class to actually process requests.
    This is typically a subclass of BaseHTTPRequestHandler. In order to use it you must
    override at least one of do_GET or do_POST.

    Args:
      server_class: the name of the server class to instantiate for the web server.
      handler_class: the name of the class to use for the RequestHandler.
      port: the port to listen on, must be greater than 1024.
    """
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    ### TLS
    if use_ssl:
        logging.info("    Wrapping HTTP with TLS on port " + str(port) + "\n")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('localhost.pem', 'localhost.pem')
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    ### END TLS

    logging.info('Starting httpd... on port ' + str(port) + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()

    logging.info('Stopping httpd...\n')


if __name__ == '__main__':

    # Set the server to enable or disable
    # specific account checking in the validation service:
    CCTransaction.enableAuthorizationChecks = True

    httpd_http = threading.Thread(group=None, target=run, name="http",
                                  kwargs={"server_class": HTTPServer,
                                          "handler_class": HTTPRequestHandler,
                                          "port": cc_validation_port,
                                          "use_ssl": False})
    httpd_https = threading.Thread(group=None, target=run, name="https",
                                   kwargs={"server_class": HTTPServer,
                                           "handler_class": HTTPRequestHandler,
                                           "port": cc_validation_port_ssl,
                                           "use_ssl": True})

    httpd_http.start()
    httpd_https.start()
