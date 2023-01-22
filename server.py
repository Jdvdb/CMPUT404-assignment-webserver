#  coding: utf-8
import socketserver
import os
import time
import calendar

# http response format: https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages

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

    # handle an HTTP request
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print("Got a request of: %s\n" % self.data)

        request = self.data.decode()
        request_info = request.split('\r\n')[0].split()

        # fill the payload with an error if improper request or POST/DELETE/PUT
        payload = self.__test_validity(request_info)

        # handle get requests
        if payload == b'':
            payload = self.__prepare_response(request_info[1])

        # send the payload
        self.request.sendall(payload)

    # return a payload with the requested file if it exists
    def __prepare_response(self, directory):
        # determine if the path provided exists
        request_path = 'www' + directory
        path_exists = os.path.exists(request_path)
        response = b''
        if path_exists:
            is_file = os.path.isfile(request_path)
            # handle location if it seems like a directory
            if not is_file and request_path[-1] == '/':
                request_path += 'index.html'

                # ensure there is an index.html in this directory
                is_file = os.path.isfile(request_path)
                if not is_file:
                    return b'HTTP/1.1 404 Not Found\r\n'

            # handle directories requested without a '/'
            elif not is_file and request_path[-1] != '/':
                date = self.__date_header()
                return b'HTTP/1.1 301 Moved Permanently\r\n' + date + b'Location: ' + directory.encode('utf-8') + b'/\r\n\r\n'

            # get file contents
            file = open(request_path)
            contents = file.read().encode('utf-8')
            file.close()

            # get the headers
            content_type = self.__content_type_header(
                request_path.split('/')[-1])
            date = self.__date_header()
            length = b'Content Length: ' + \
                str(len(contents)).encode('utf-8') + b'\r\n'

            # create the response
            response = b'HTTP/1.1 200 Ok\r\n' + date + \
                content_type + length + b'\r\n' + contents
            return response

        else:
            return b'HTTP/1.1 404 Not Found\r\n'

    # determine if request is properly structured as 'GET' and not suspicious with location
    def __test_validity(self, request_info):
        if len(request_info) != 3:
            return b'HTTP/1.1 400 Bad Request\r\n'
        if request_info[0] != 'GET':
            if request_info[0] == 'POST' or request_info[0] == 'DELETE' or request_info[0] == 'PUT':
                return b'HTTP/1.1 405 Method Not Allowed\r\n'
        if request_info[2] != 'HTTP/1.1':
            return b'HTTP/1.1 400 Bad Request\r\n'

        # block requests trying to exit www directory
        path = request_info[1].split('/')
        current_depth = 1
        iter = 0
        while iter < len(path) and current_depth > 0:
            if path[iter] == '..':
                current_depth -= 1
            else:
                current_depth += 1
            iter += 1

        if current_depth == 0:
            return b'HTTP/1.1 404 Not Found'
        return b''

    # create header with date
    def __date_header(self):
        # https://pynative.com/python-get-the-day-of-week/#h-get-the-weekday-name-from-date-using-calendar-module
        date = time.gmtime(time.time())
        formatted_date = "{}, {} {} {} {}:{}:{} GMT".format(
            calendar.day_name[date.tm_wday][0:3], date.tm_mday, calendar.month_name[date.tm_mon][0:3], date.tm_year, date.tm_hour, date.tm_min, date.tm_sec)
        return b'Date: ' + formatted_date.encode('utf-8') + b'\r\n'

    # generate content type header
    def __content_type_header(self, file_name):
        response = b'Content-Type:'
        file_type = file_name.split('.')[-1]
        if file_type == 'html':
            return response + b' text/html\r\n'
        elif file_type == 'css':
            return response + b' text/css\r\n'
        else:
            return response + b' text\r\n'


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
