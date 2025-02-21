import sys
import threading
from common.control_block import ControlBlock
from file_share.upload import upload_file
from file_share.send_recv_tcp import request_file_from_peer
from peer_discovery.discovery import (
    listen_for_broadcast_and_handle_requests,
    send_broadcast,
    search_for_file_within_peers,
)
from common.debug_print import printfunc


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
            printfunc("Available commands:")
            printfunc("  - help: Display this help message.")
            printfunc("  - upload: Upload a file.")
            printfunc("  - download: Download a file from a peer.")
            printfunc("  - exit: Exit the program.")

        elif command == "upload":
            filename = input("Enter the absolute path of the file you want to upload: ")
            upload_file(control_blk, filename)  # Upload the file to ControlBlock

        elif command == "download":
            filename = input("Enter the name of the file you want to download: ")
            peers = search_for_file_within_peers(control_blk, filename)
            if not peers:
                printfunc(f"File '{filename}' not found within peers currently.")
            else:
                request_file_from_peer(peers[0], filename)

        elif command == "exit":
            printfunc("Exiting the program.")
            break

        elif command == "debug":
            printfunc("Debugging Information:")
            printfunc(f"Peer List: {control_blk.peer_list}")
            printfunc(f"Peer to File Mapping: {control_blk.peer_to_file}")
            printfunc(f"Local File List: {control_blk.file_list}")

        else:
            printfunc(
                f"Unknown command: '{command}'. Type 'help' for a list of commands."
            )


def main():
    # Create the ControlBlock instance
    control_blk = ControlBlock()

    # Start the peer discovery thread
    peer_discovery_thread = threading.Thread(
        target=listen_for_broadcast_and_handle_requests, args=(control_blk,)
    )
    peer_discovery_thread.daemon = True
    peer_discovery_thread.start()

    broadcast_thread = threading.Thread(target=send_broadcast)
    broadcast_thread.daemon = True
    broadcast_thread.start()

    # Main thread handles user input
    handle_user_input(control_blk)

    # Wait for any remaining background tasks to complete (if needed)
    # In this case, the peer discovery thread is a daemon, so it will exit when the main thread exits


if __name__ == "__main__":
    main()
