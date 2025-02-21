import sys
import threading
from common.control_block import ControlBlock
from file_share.upload import upload_file

# from file_share.send_recv_tcp import search_file_from_peer
from peer_discovery.discovery import (
    listen_for_broadcast_and_handle_requests,
    send_broadcast,
    search_for_file_within_peers,
)
from common.debug_print import debug_print


def handle_user_input(control_blk: ControlBlock) -> None:
    """
    Main thread function to process user commands.
    """
    while True:
        # Get user input in the main thread
        command = (
            input("\nEnter a command (help, upload, download, exit): ").strip().lower()
        )

        if command == "help":
            debug_print("Available commands:")
            debug_print("  - help: Display this help message.")
            debug_print("  - upload: Upload a file.")
            debug_print("  - download: Download a file from a peer.")
            debug_print("  - exit: Exit the program.")

        elif command == "upload":
            filename = input("Enter the absolute path of the file you want to upload: ")
            upload_file(control_blk, filename)  # Upload the file to ControlBlock

        elif command == "download":
            filename = input("Enter the name of the file you want to download: ")
            peers = search_for_file_within_peers(control_blk, filename)
            if not peers:
                debug_print(f"File '{filename}' not found within peers currently.")
            else:
                # TODO
                debug_print("peer found.")

        elif command == "exit":
            debug_print("Exiting the program.")
            break

        elif command == "debug":
            debug_print("Debugging Information:")
            debug_print(f"Peer List: {control_blk.peer_list}")
            debug_print(f"Peer to File Mapping: {control_blk.peer_to_file}")
            debug_print(f"Local File List: {control_blk.file_list}")

        else:
            debug_print(
                f"Unknown command: '{command}'. Type 'help' for a list of commands."
            )


def main():
    # Create the ControlBlock instance
    control_blk = ControlBlock()
    thread_var = threading.Event()

    peer_discovery_thread = threading.Thread(
        target=listen_for_broadcast_and_handle_requests,
        args=(
            thread_var,
            control_blk,
        ),
    )
    peer_discovery_thread.daemon = True
    peer_discovery_thread.start()

    broadcast_thread = threading.Thread(target=send_broadcast, args=(thread_var,))
    broadcast_thread.daemon = True
    broadcast_thread.start()

    # Main thread handles user input
    handle_user_input(control_blk)


if __name__ == "__main__":
    main()
