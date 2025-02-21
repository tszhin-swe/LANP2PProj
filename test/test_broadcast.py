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
from src.peer_discovery.discovery import (
    send_broadcast,
    listen_for_broadcast_and_handle_requests,
)
from src.common.debug_print import printfunc
from src.common.global_thread_event import SingletonEvent


class TestPeerDiscovery(unittest.TestCase):

    def setUp(self):
        # Initialize the threading event in setUp to ensure it's created before each test
        self.threading_event = threading.Event()
        self.threading_event.clear()  # Ensure the event is cleared before each test

    def run_peer(self, control_blk: ControlBlock):
        """Simulate a peer broadcasting and listening for discovery."""
        # Simulate peer broadcasting
        broadcaster_thread = threading.Thread(
            target=send_broadcast, args=(self.threading_event,)
        )
        broadcaster_thread.daemon = True  # Allow thread to exit when main program exits
        broadcaster_thread.start()

        # Give broadcaster a moment to start
        time.sleep(1)

        # Simulate peer listening for discovery
        listener_thread = threading.Thread(
            target=listen_for_broadcast_and_handle_requests,
            args=(
                self.threading_event,
                control_blk,
            ),
        )
        listener_thread.daemon = True  # Allow thread to exit when main program exits
        listener_thread.start()

        # Allow time for peer discovery
        time.sleep(10)

        # Return the threads for joining later
        return broadcaster_thread, listener_thread

    def test_peer_discovery(self):
        """Test peer discovery between peers using threads."""

        # Create a ControlBlock instance to track discovered peers
        control_blk = ControlBlock()
        # Start the discovery simulation (run broadcasting and listening in separate threads)
        broadcaster_thread, listener_thread = self.run_peer(control_blk)

        # Check if at least one peer has been discovered
        printfunc(f"Discovered peers: {control_blk.peer_list}")
        self.assertGreater(len(control_blk.peer_list), 0, "No peers discovered!")

        self.threading_event.set()  # Signal threads to stop

        # Cleanup threads
        listener_thread.join(timeout=5)
        broadcaster_thread.join(timeout=5)

    def tearDown(self):
        """Clean up resources after each test run."""
        # Any necessary cleanup, like closing sockets or stopping threads
        printfunc("Cleaning up resources after test.")


if __name__ == "__main__":
    unittest.main()
