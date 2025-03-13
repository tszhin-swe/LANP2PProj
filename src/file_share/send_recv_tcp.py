import socket
import os
import hashlib
from common.debug_print import debug_print, regular_print
from common.control_block import ControlBlock
from peer_discovery.discovery import MY_SERVER_PORT

FILE_PORT = 60000  # Port for file transfer
BUFFER_SIZE = 1024  # Chunk size for file transfer


def get_hash_of_file(file_name: str):
    hasher = hashlib.sha256()
    with open(file_name, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def send_file(cb: ControlBlock, client_socket: socket.socket, file_name: str):
    # Check if the file exists and can be sent
    file_name_path = cb.get_file_path(file_name)
    if os.path.exists(file_name_path):
        client_socket.send(b"FILE_FOUND")  # Send file found message
        client_socket.send(
            get_hash_of_file(file_name_path).encode()
        )  # Send hash of file
        # Send the file in chunks
        with open(file_name_path, "rb") as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.send(chunk)
        regular_print(f"Sent {file_name} to {client_socket.getpeername()}")
    else:
        client_socket.send(b"FILE_NOT_FOUND")  # Send file not found message

    client_socket.close()


def start_file_server(cb: ControlBlock):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server_socket.bind(("", MY_SERVER_PORT))
    server_socket.listen(5)  # Allow up to 5 connections

    debug_print("File server listening on port", MY_SERVER_PORT)

    while True:
        client_socket, client_address = server_socket.accept()
        debug_print(f"Connection established with {client_address}")

        # Receive the file name from the client
        file_name = client_socket.recv(BUFFER_SIZE).decode()

        send_file(cb, client_socket, file_name)


BUFFER_SIZE = 1024  # Chunk size for file transfer


def get_server_addr_from_peer_addr(peer_ip: str, port: int):
    return (peer_ip, port + 10000)


def receive_file_from_peer(peer_ip: tuple, file_name: str):
    address = get_server_addr_from_peer_addr(peer_ip[0], peer_ip[1])
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address)

    # Send the file name to the peer
    client_socket.send(file_name.encode())

    # Wait for response (whether file exists or not)
    response = client_socket.recv(BUFFER_SIZE).decode()

    if response == "FILE_FOUND":
        hash_of_file = client_socket.recv(BUFFER_SIZE).decode()
        regular_print(f"Receiving file {file_name} from {peer_ip}...")

        with open(f"downloaded_{file_name}", "wb") as file:
            while True:
                # Receive the file in chunks
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                file.write(data)

        # Check if the file is valid
        print(hash_of_file, get_hash_of_file(f"downloaded_{file_name}"))
        if hash_of_file == get_hash_of_file(f"downloaded_{file_name}"):
            regular_print(f"File {file_name} downloaded successfully.")
        else:
            regular_print(f"File {file_name} checksum incorrect.")
    else:
        regular_print(f"File {file_name} not found on {peer_ip}.")

    client_socket.close()
