import socket
import os
from common.debug_print import debug_print


FILE_PORT = 60000  # Port for file transfer
BUFFER_SIZE = 1024  # Chunk size for file transfer


def handle_file_request(client_socket: socket.socket, file_name: str):
    # Check if the file exists
    if os.path.exists(file_name):
        client_socket.send(b"FILE_FOUND")  # Send file found message

        # Send the file in chunks
        with open(file_name, "rb") as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.send(chunk)
        debug_print(f"Sent {file_name} to {client_socket.getpeername()}")
    else:
        client_socket.send(b"FILE_NOT_FOUND")  # Send file not found message

    client_socket.close()


def start_file_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", FILE_PORT))
    server_socket.listen(5)  # Allow up to 5 connections

    debug_print("File server listening on port", FILE_PORT)

    while True:
        client_socket, client_address = server_socket.accept()
        debug_print(f"Connection established with {client_address}")

        # Receive the file name from the client
        file_name = client_socket.recv(BUFFER_SIZE).decode()

        # Handle file request
        handle_file_request(client_socket, file_name)


BUFFER_SIZE = 1024  # Chunk size for file transfer


def request_file_from_peer(peer_ip: str, file_name: str):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((peer_ip, FILE_PORT))

    # Send the file name to the peer
    client_socket.send(file_name.encode())

    # Wait for response (whether file exists or not)
    response = client_socket.recv(BUFFER_SIZE).decode()

    if response == "FILE_FOUND":
        debug_print(f"Receiving file {file_name} from {peer_ip}...")

        with open(f"downloaded_{file_name}", "wb") as file:
            while True:
                # Receive the file in chunks
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                file.write(data)
        debug_print(f"File {file_name} downloaded successfully.")
    else:
        debug_print(f"File {file_name} not found on {peer_ip}.")

    client_socket.close()
