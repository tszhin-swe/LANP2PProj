import threading


def debug_print(*args, **kwargs):
    """Custom debug_print function that prefixes output with the current thread ID or name."""
    thread_name = threading.current_thread().name
    print(f"[Thread-{thread_name}] ", *args, **kwargs)
