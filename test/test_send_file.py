import unittest
import threading
import time
import socket
import sys
import os
import hashlib

# Add the src directory to the Python module search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.common.control_block import ControlBlock
from src.common.debug_print import debug_print, regular_print
from src.peer_discovery.discovery import (
    send_broadcast,
    listen_for_broadcast_and_handle_requests,
    search_for_file_within_peers,
)
from src.file_share.send_recv_tcp import start_file_server, receive_file_from_peer

MY_FILE_REQUEST_PORT = 50001 + (os.getpid() % 10)


class TestSendFile(unittest.TestCase):
    def assert_files_equal(self, file1: str, file2: str):
        """Asserts that two files contain the same content."""

        def file_hash(filepath):
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                print(filepath)
                while chunk := f.read(8192):
                    print(filepath, chunk)
                    hasher.update(chunk)
            return hasher.hexdigest()

        hash1, hash2 = file_hash(file1), file_hash(file2)

    def setUp(self):
        # Initialize the threading event in setUp to ensure it's created before each test
        self.threading_event = threading.Event()
        self.threading_event.clear()  # Ensure the event is cleared before each test

    def server_thread_server_for_send_file(self, control_blk: ControlBlock):
        start_file_server(control_blk)

    def client_thread_recv_file(self, addr: tuple, filename: str):
        receive_file_from_peer(addr, filename)

    def test_send_file_success(self):
        """Test file finding between peers using threads."""
        client_control_block = ControlBlock()
        server_addr = ("10.0.0.103", MY_FILE_REQUEST_PORT)
        server_control_block = ControlBlock()
        server_control_block.file_list = ["test/test.txt"]
        """Simulate a peer broadcasting and listening for discovery."""
        server_thread = threading.Thread(
            target=self.server_thread_server_for_send_file, args=(server_control_block,)
        )
        server_thread.daemon = True  # Allow thread to exit when main program exits
        server_thread.start()

        # Give broadcaster a moment to start
        time.sleep(1)

        client_thread = threading.Thread(
            target=self.client_thread_recv_file,
            args=(
                server_addr,
                "test.txt",
            ),
        )
        client_thread.daemon = True  # Allow thread to exit when main program exits
        client_thread.start()
        self.assert_files_equal("test/test.txt", "downloaded_test.txt")
        time.sleep(10)
        self.threading_event.set()  # Signal threads to stop

        # Cleanup threads
        server_thread.join(timeout=5)
        client_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
