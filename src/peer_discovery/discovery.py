import socket
import time
import os
import threading
import select
from typing import List
from common.control_block import ControlBlock
from common.debug_print import debug_print, regular_print

BROADCAST_IP = "255.255.255.255"  # Limited broadcast address, sending to this address broadcasts to all devices within LAN.
BROADCAST_PORT = 50000  # Port to broadcast to
MESSAGE = b"HELLO_PEER"  # Message to broadcast
FILE_REQUEST_MESSAGE = b"REQUEST_FILE"

"""Listen for UDP broadcasts and handle file requests on a specific port."""
MY_FILE_REQUEST_PORT = 50001 + (os.getpid() % 10)  # Each process gets a unique port


def close_socket(sock):
    debug_print("Closing socket...")
    try:
        sock.close()
    except Exception as e:
        debug_print(f"Error closing socket: {e}")


# TODO: Consider debug mode (filtering out the correct local ip will make local threads communication fail)
# Function to get the local network IP address (non-loopback)
def get_local_ip():
    return 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This will retrieve the local IP by trying to connect to an external address
        s.connect(("8.8.8.8", 80))  # Google's public DNS, any external server will work
        local_ip = s.getsockname()[0]
    except Exception:
        # Fallback to using gethostname if external connection fails
        local_ip = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()
    return local_ip


"""Broadcasts a message periodically to all devices in the local network with UDP."""

def send_broadcast(threading_event: threading.Event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Enable broadcasting
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        while not threading_event.is_set():
            # Include file request port in broadcast message
            message = f"{MESSAGE.decode()} {MY_FILE_REQUEST_PORT}".encode()
            sock.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
            debug_print(f"Broadcasting message: {message.decode()}")

            time.sleep(5)  # Broadcast every 5 seconds
    finally:
        print("Finishing broadcasting...")
        close_socket(sock)


BUFFER_SIZE = 1024  # Buffer size for receiving messages


def handle_file_request(control_blk, sock, data, addr):
    debug_print(f"Received message: {data.decode()} from {addr}")
    requested_file = data.decode()[len(FILE_REQUEST_MESSAGE.decode()) :].strip()
    debug_print(f"Received file request for {requested_file} from {addr}")

    # Check if the file exists
    if control_blk.check_file_available(requested_file):
        # Respond with FILE_AVAILABLE if the file exists
        response = b"FILE_AVAILABLE"
        sock.sendto(response, addr)
        debug_print(f"Sent file availability response to {addr}")
    else:
        # Respond with a message indicating the file is not available
        response = b"FILE_NOT_AVAILABLE"
        sock.sendto(response, addr)
        debug_print(f"Sent file not available response to {addr}")

def listen_for_broadcast_and_handle_requests(threading_event: threading.Event, control_blk: ControlBlock):
    broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    broadcast_sock.bind(("0.0.0.0", BROADCAST_PORT))

    file_request_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    file_request_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    file_request_sock.bind(("0.0.0.0", MY_FILE_REQUEST_PORT))

    debug_print(f"Listening on {BROADCAST_PORT} for broadcasts and {MY_FILE_REQUEST_PORT} for file requests.")

    try:
        while not threading_event.is_set():
            ready_sockets, _, _ = select.select([broadcast_sock, file_request_sock], [], [], 5)

            for sock in ready_sockets:
                data, addr = sock.recvfrom(BUFFER_SIZE)

                if sock == broadcast_sock:
                    message = data.decode().strip().split()
                    if len(message) == 2 and message[0] == "HELLO_PEER":
                        peer_ip, peer_port = addr[0], int(message[1])
                        
                        # Avoid adding self to the peer list
                        if (peer_ip, peer_port) not in control_blk.peer_list:
                            debug_print(f"Adding peer {peer_ip} with file request port {peer_port}")
                            control_blk.peer_list.append((peer_ip, peer_port))
                
                elif sock == file_request_sock:
                    if data.decode().startswith(FILE_REQUEST_MESSAGE.decode()):
                        handle_file_request(control_blk, file_request_sock, data, addr)

    finally:
        close_socket(broadcast_sock)
        close_socket(file_request_sock)
"""Request a file from a peer and return whether the file is available."""


def search_file_from_peer(peer_address: tuple, filename: str) -> bool:
    # Create a UDP socket to send the request
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        # Construct the request message
        request_message = f"{FILE_REQUEST_MESSAGE.decode()} {filename}".encode()

        # Send the request to the peer's address
        sock.sendto(request_message, peer_address)
        debug_print(f"Check if '{filename}' is in {peer_address}")

        # Set a timeout to receive the response (in case the file is not available)
        sock.settimeout(5)  # Wait for 5 seconds for a response

        try:
            # Wait for the peer's response (whether file is available or not)
            data, _ = sock.recvfrom(BUFFER_SIZE)
            if data.decode() == "FILE_AVAILABLE":
                debug_print(f"File '{filename}' is available from {peer_address}.")
                return True
            else:
                debug_print(f"Peer {peer_address} responded with no file.")
                return False
        except socket.timeout:
            debug_print(f"Request timed out for {filename} from {peer_address}.")
            return False

    finally:
        close_socket(sock)


def search_for_file_within_peers(cb: ControlBlock, filename: str) -> List[tuple]:
    peer_list = cb.peer_list.copy() # TODO: Fix this
    for peer in peer_list:
        addr = (peer[0], BROADCAST_PORT)
        if search_file_from_peer(peer, filename):
            return [peer]
    cb.peer_list = peer_list
    return []
