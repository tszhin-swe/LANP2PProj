import threading


class SingletonEvent:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:  # Ensure that only one thread can create the instance at a time
            if cls._instance is None:
                print(
                    f"Creating SingletonEvent instance in thread {threading.current_thread().name}"
                )
                cls._instance = super(SingletonEvent, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Ensure initialization only happens once
        if not self._initialized:
            print(
                f"Initializing SingletonEvent instance in thread {threading.current_thread().name}"
            )
            self.event = threading.Event()
            self._initialized = True

    def get_event(self):
        return self.event
