import socket
import os
import hashlib
from common.debug_print import debug_print, regular_print
from common.control_block import ControlBlock
from peer_discovery.discovery import MY_SERVER_PORT
import threading

FILE_PORT = 60000  # Port for file transfer
BUFFER_SIZE = 1024  # Chunk size for file transfer


def get_hash_of_file(file_name: str):
    hasher = hashlib.sha256()
    with open(file_name, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def send_file(cb, client_socket, file_name, start, end):
    """Send only the requested segment of a file."""
    try:
        file_path = cb.get_file_path(file_name)
        if not os.path.exists(file_path):
            client_socket.send("FILE_NOT_FOUND".encode())
            return

        file_size = os.path.getsize(file_path)
        if start >= file_size or end > file_size or start >= end:
            client_socket.send("INVALID_RANGE".encode())
            return

        client_socket.send("FILE_FOUND".encode())

        # Send hash of the segment (optional)
        segment_hash = get_hash_of_file(file_path)
        client_socket.send(segment_hash.encode())

        # Send the requested segment
        with open(file_path, "rb") as file:
            file.seek(start)
            remaining = end - start
            while remaining > 0:
                data = file.read(min(BUFFER_SIZE, remaining))
                if not data:
                    break
                client_socket.send(data)
                remaining -= len(data)

    except Exception as e:
        print(f"Error sending file: {e}")
        client_socket.send("ERROR".encode())

    finally:
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

        request_message = client_socket.recv(BUFFER_SIZE).decode()
        parts = request_message.split(":")
        if len(parts) != 3:
            client_socket.send("INVALID_REQUEST".encode())
            continue

        file_name, start, end = parts[0], int(parts[1]), int(parts[2])
        send_file(cb, client_socket, file_name, start, end)


BUFFER_SIZE = 1024  # Chunk size for file transfer


def get_server_addr_from_peer_addr(peer_ip: str, port: int):
    return (peer_ip, port + 10000)


def receive_segment_from_peer(
    peer_ip: tuple, file_name: str, start, end, output_file, lock
):
    """Download a specific segment of a file from a peer."""
    address = get_server_addr_from_peer_addr(peer_ip[0], peer_ip[1])
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect(address)
        request_message = f"{file_name}:{start}:{end}"
        client_socket.send(request_message.encode())

        response = client_socket.recv(BUFFER_SIZE).decode()
        if response != "FILE_FOUND":
            print(f"Segment {start}-{end} not found on {peer_ip}.")
            return

        hash_of_segment = client_socket.recv(BUFFER_SIZE).decode()
        print(f"Receiving segment {start}-{end} of {file_name} from {peer_ip}...")

        with open(output_file, "r+b") as file:
            file.seek(start)  # Move to the correct position
            remaining = end - start
            while remaining > 0:
                data = client_socket.recv(min(BUFFER_SIZE, remaining))
                if not data:
                    break
                with lock:
                    file.write(data)
                remaining -= len(data)

        if hash_of_segment == get_hash_of_file(output_file):
            print(f"Segment {start}-{end} verified.")
        else:
            print(f"Segment {start}-{end} corrupted.")

    except Exception as e:
        print(f"Error receiving segment {start}-{end} from {peer_ip}: {e}")

    finally:
        client_socket.close()


def receive_file_from_peers(peers: list, file_name: str):
    # Ensure all peers have the same file size
    file_sizes = {peer[1] for peer in peers}
    if len(file_sizes) != 1:
        print("Peer list is not consistent. Cannot download file.")
        return

    file_size = file_sizes.pop()
    num_peers = len(peers)
    segment_size = file_size // num_peers
    output_file = f"downloaded_{file_name}"
    with open(output_file, "wb") as f:
        f.truncate(file_size)

    lock = threading.Lock()

    threads = []
    for i, (peer, _) in enumerate(peers):
        start = i * segment_size
        end = file_size if i == num_peers - 1 else (i + 1) * segment_size

        thread = threading.Thread(
            target=receive_segment_from_peer,
            args=(peer, file_name, start, end, output_file, lock),
        )
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print(f"File {file_name} successfully downloaded from peers.")


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
