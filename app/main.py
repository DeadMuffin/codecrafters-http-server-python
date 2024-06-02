'''
Simple HTTP server that supports some GET and POST requests
Created while doing the CodeCrafter challenge
'''

import gzip
from io import BytesIO
import socket
import argparse

def decode_request(request):
    '''Decodes a request from a client into a dictionary'''
    print("bytes Request:", request)
    data = request.decode("utf-8")
    start, *headers, body = data.split("\r\n")
    method, path, version = start.split()
    headers_dict = {}
    for header in headers:
        if not header == "":
            key, value = header.split(": ",1)
            headers_dict[key.lower()] = value
    return {
        "method": method.lower(),
        "path": path,
        "version": version,
        "headers": headers_dict,
        "body": body
    }

def handle_request(request, directory=None):
    '''
    Handles a request from a client and returns a response
    
    Args:
        request: A dictionary containing the request data
        directory: The directory to save files to
    Supported methods:
        - GET
            - /
            - /echo/<text> (optional: ?accept-encoding=gzip)
            - /user-agent
            - /files/<filename>
        - POST
            - /files/<filename>
    '''
    print("Request:", request)

    if request["method"] == "get":
        if request["path"] == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"
        elif "echo" in request["path"]:
            paths = request["path"].split("/")

            if "accept-encoding" in request["headers"] and "gzip" in request["headers"]["accept-encoding"]:
                # Create a buffer to hold the gzip data
                buffer = BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
                    f.write(paths[2].encode())

                # Get the gzip-encoded content
                encoded = buffer.getvalue()
                response = f"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Type: text/plain\r\nContent-Length: {len(encoded)}\r\n\r\n".encode() + encoded  
            else:
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(paths[2])}\r\n\r\n{paths[2]}".encode()
        elif "user-agent" in request["path"]:    
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(request['headers']['user-agent'])}\r\n\r\n{request['headers']['user-agent']}".encode()
        elif directory and "files" in request["path"]:
            paths = request["path"].split("/")
            try:
                data = b""
                with open(f"{directory}/{paths[2]}", "rb") as file:
                    data += file.read()
                response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(data)}\r\n\r\n".encode() + data
            except FileNotFoundError:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"
        else:
            response = b"HTTP/1.1 404 Not Found\r\n\r\n"
    elif request["method"] == "post":
        if directory and "files" in request["path"]:
            paths = request["path"].split("/")
            try:
                with open(f"{directory}/{paths[2]}", "w") as file:
                    file.write(request["body"])
                response = b"HTTP/1.1 201 Created\r\n\r\n"
            except FileNotFoundError:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"
    else:
        response = b"HTTP/1.1 405 Method Not Allowed\r\n\r\n"
    
    print(f"Sending response: {response}")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str)
    args = parser.parse_args()
    directory = args.directory


    print("Starting server")
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        client_socket, address = server_socket.accept()
        print(f"Connection accepted from {address}")
        client_socket.sendall(handle_request(decode_request(client_socket.recv(4096)), directory))
if __name__ == "__main__":
    main()
