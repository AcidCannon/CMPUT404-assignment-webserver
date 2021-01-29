#  coding: utf-8 
import socketserver
import os
import mimetypes
# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

class MyWebServer(socketserver.BaseRequestHandler):
    def handle(self):
        # CONSTANTS
        self.VALID_COMMANDS = ["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH",\
                               "OPTIONS", "TRACE", "CONNECT"]
        self.ALLOWED_COMMANDS = ["GET"]
        self.DEBUG = False
        self.INDEX = "index.html"
        self.ROOT = "./www"
        self.SCHEME = "http://"
        self.handle_root()
        
        self.data = self.request.recv(1024).strip()
        recv = self.data.decode("utf-8").split()
        if self.DEBUG: print ("Got a request of: %s\n" % recv)
        # See README section "Flow" to know why I have so many if's :)
        try:
            if recv[0] in self.VALID_COMMANDS:  
                if recv[0] in self.ALLOWED_COMMANDS:
                    if recv[1][-1] == "/":
                        if self.is_safe(recv[1]):
                            if os.path.exists(f"{self.ROOT}{recv[1]}/{self.INDEX}"):
                                # directory exist, display index.html
                                self.request.sendall(self.status_code_200(f"{recv[1]}/{self.INDEX}"))
                            else:
                                self.request.sendall(self.status_code_404())
                        else:
                            # I personally think a status 403 Forbidden will be better
                            # Since viewing parent directory need higher permission
                            self.request.sendall(self.status_code_404())
                    else:
                        if self.is_safe(recv[1]):
                            if os.path.isfile(f"{self.ROOT}{recv[1]}"):
                                # file exist, display
                                self.request.sendall(self.status_code_200(recv[1]))
                            else:
                                # directory exist, 301 redirect
                                self.request.sendall(self.status_code_301(recv[1]))
                        else:
                            self.request.sendall(self.status_code_404())
                else:
                    # Command disallowed
                    self.request.sendall(self.status_code_405())
            else:
                # Not even a valid command, a bad request
                self.request.sendall(self.status_code_400())
        except IndexError:
            pass

    def status_code_400(self):
        # Bad Request
        return bytearray("HTTP/1.1 400 Bad Request\r\n", "utf-8")
    
    def status_code_405(self):
        # Method Not Allowed
        return bytearray("HTTP/1.1 405 Method Not Allowed\r\nContent-type: text/html\r\n\r\n<h1>Method Not Allowed</h1>", "utf-8")

    def status_code_404(self):
        # Not Found
        return bytearray("HTTP/1.1 404 Not Found\r\nContent-type: text/html\r\n\r\n<h1>Not found</h1>", "utf-8")

    def status_code_500(self):
        # Internal Server Error
        return bytearray("HTTP/1.1 500 Internal Server Error\r\n", "utf-8")

    def status_code_200(self, path):
        # OK
        # https://www.tutorialspoint.com/How-to-find-the-mime-type-of-a-file-in-Python, Author: Rajendra Dharmkar, Published on 27-Dec-2017 15:55:12
        # https://www.geeksforgeeks.org/python-os-path-basename-method/#:~:text=basename()%20method%20in%20Python,pair%20(head%2C%20tail)., Author: ihritik, Last Updated : 26 Aug, 2019
        mimetype = mimetypes.MimeTypes().guess_type(os.path.basename(path))[0]
        try:
            with open(self.ROOT + path, "r") as f:
                content = f.read()
                if self.DEBUG: return bytearray(f"HTTP/1.1 200 OK\r\nCache-Control: no-cache\r\nContent-type:{mimetype}\r\n\r\n{content}", "utf-8")
                return bytearray(f"HTTP/1.1 200 OK\r\nContent-type:{mimetype}\r\n\r\n{content}", "utf-8")
        except:
            # Error(s) occured while reading file :(
            return bytearray(self.status_code_500())
    
    def status_code_301(self, path):
        # There is a potential issue in unit test provided to us, BASEURL has been hardcoded => "http://127.0.0.1:8080"
        # If you use "http://localhost:8080"(as I did in line 113, I am pretty sure it will work) but test will fail
        # By convention, localhost is the hostname of local loopback 127.0.0.1
        # return bytearray(f"HTTP/1.1 301 Moved Permanently\r\nLocation: {self.SCHEME}{HOST}:{PORT}{path}/\r\n", "utf-8")
        return bytearray(f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path}/\r\n", "utf-8")
    
    def status_code_403(self):
        # Forbidden
        return bytearray("HTTP/1.1 403 Forbidden\r\n", "utf-8")
        
    def is_safe(self, path):
        if self.DEBUG: print(f"ABS_ROOT:{self.ROOT}, REL_REQ_DIR: {path}, ABS_REQ_DIR: {os.path.abspath(self.ROOT + path)}")
        # Path is safe iff the commonprefix of absolute path of root for content == path of the request
        # https://stackoverflow.com/questions/45188708/how-to-prevent-directory-traversal-attack-from-python-code, Author: kabanus, Answered Jul 19 '17 at 11:13
        # https://stackoverflow.com/questions/37863476/why-would-one-use-both-os-path-abspath-and-os-path-realpath, Author: jobrad, Answered Oct 28 '16 at 18:29
        if os.path.commonprefix([os.path.abspath(f"{self.ROOT}{path}"), self.ROOT]) == self.ROOT:
            return True
        return False
    
    def handle_root(self):
        # Transform relative path to absolute path for later use
        self.ROOT = os.path.realpath(self.ROOT)
        

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
