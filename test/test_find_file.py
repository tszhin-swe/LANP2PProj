import unittest
import threading
import time
import socket
import sys
import os


# Add the src directory to the Python module search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.common.control_block import ControlBlock
from src.common.debug_print import debug_print
from src.peer_discovery.discovery import (
    send_broadcast,
    listen_for_broadcast_and_handle_requests,
    search_for_file_within_peers,
)

PORT = 50000


class TestFileFind(unittest.TestCase):

    def setUp(self):
        # Initialize the threading event in setUp to ensure it's created before each test
        self.threading_event = threading.Event()
        self.threading_event.clear()  # Ensure the event is cleared before each test

    def server_thread_send_file(self, control_blk: ControlBlock):
        debug_print(f"Server: {control_blk.file_list}")
        listen_for_broadcast_and_handle_requests(self.threading_event, control_blk)

    def client_thread_look_for_peer_with_file(
        self, control_blk: ControlBlock, filename: str, assert_func
    ):
        peers_with_file = search_for_file_within_peers(control_blk, filename)
        assert_func(peers_with_file)

    def test_find_nonexistent_file(self):
        client_control_block = ControlBlock()
        client_control_block.peer_list = [("10.0.0.103", PORT)]
        server_control_block = ControlBlock()
        """Simulate a peer broadcasting and listening for discovery."""
        broadcaster_thread = threading.Thread(
            target=self.server_thread_send_file, args=(server_control_block,)
        )
        broadcaster_thread.daemon = True  # Allow thread to exit when main program exits
        broadcaster_thread.start()

        # Give broadcaster a moment to start
        time.sleep(1)

        # Client thread should not find anything.
        assertFileNotExist = lambda peers_with_file: self.assertEqual(
            len(peers_with_file), 0
        )
        listener_thread = threading.Thread(
            target=self.client_thread_look_for_peer_with_file,
            args=(client_control_block, "nonexistent_file.txt", assertFileNotExist),
        )
        listener_thread.daemon = True  # Allow thread to exit when main program exits
        listener_thread.start()

        time.sleep(10)

        self.threading_event.set()  # Signal threads to stop
        # Cleanup threads
        broadcaster_thread.join(timeout=5)
        listener_thread.join(timeout=5)

    def test_file_find(self):
        """Test file finding between peers using threads."""
        client_control_block = ControlBlock()
        client_control_block.peer_list = [("10.0.0.103", PORT)]
        server_control_block = ControlBlock()
        server_control_block.file_list = ["test_file.txt"]
        """Simulate a peer broadcasting and listening for discovery."""
        broadcaster_thread = threading.Thread(
            target=self.server_thread_send_file, args=(server_control_block,)
        )
        broadcaster_thread.daemon = True  # Allow thread to exit when main program exits
        broadcaster_thread.start()

        # Give broadcaster a moment to start
        time.sleep(1)

        # Client thread should not find anything.
        assertFileExist = lambda peers_with_file: self.assertEqual(
            len(peers_with_file), 1
        )
        listener_thread = threading.Thread(
            target=self.client_thread_look_for_peer_with_file,
            args=(client_control_block, "test_file.txt", assertFileExist),
        )
        listener_thread.daemon = True  # Allow thread to exit when main program exits
        listener_thread.start()

        time.sleep(10)
        self.threading_event.set()  # Signal threads to stop

        # Cleanup threads
        broadcaster_thread.join(timeout=5)
        listener_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
