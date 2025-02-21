import threading


def printfunc(*args, **kwargs):
    """Custom printfunc function that prefixes output with the current thread ID or name."""
    thread_name = threading.current_thread().name
    print(f"[Thread-{thread_name}] ", *args, **kwargs)
