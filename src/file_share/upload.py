import socket
import time
import os
from common.control_block import ControlBlock
from common.debug_print import printfunc


# filename should be provided in absolute paths.
def upload_file(control_blk: ControlBlock, filename: str):
    try:
        # Try to open the file in read mode to check if it exists
        with open(filename, "rb") as file:
            # If the file opens successfully, add it to the file list
            control_blk.file_list.append(filename)
            printfunc(f"File '{filename}' uploaded successfully.")
    except FileNotFoundError:
        # If the file is not found, printfunc an error message
        printfunc(f"Error: The file '{filename}' was not found.")
    except Exception as e:
        # Catch other exceptions and printfunc an error message
        printfunc(
            f"Error: An unexpected error occurred while uploading '{filename}': {e}"
        )
