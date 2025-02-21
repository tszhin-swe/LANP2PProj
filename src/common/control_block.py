from typing import List, Dict


class ControlBlock:
    """
    A class representing a control block for managing peer-to-peer file sharing.

    Attributes:
        peer_list (List[str]): A list of IP addresses (or identifiers) of peers.
        peer_to_file (Dict[str, List[str]]): A dictionary mapping peer IPs to a list of files they have.
        file_list (List[str]): A list of filenames shared by the local peer.
    """

    def __init__(self) -> None:
        self.peer_list: List[str] = []
        self.peer_to_file: Dict[str, List[str]] = {}
        self.file_list: List[str] = []

    def check_file_available(self, filename: str) -> bool:
        for file in self.file_list:
            if file.split("/")[-1] == filename:
                return True
        return False

    def get_file_path(self, filename: str) -> str:
        for file in self.file_list:
            if file.split("/")[-1] == filename:
                return file
        return ""
