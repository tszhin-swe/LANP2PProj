import threading

DEBUG = False


def debug_print(*args, **kwargs):
    """Custom debug_print function that prefixes output with the current thread ID or name."""
    if not DEBUG:
        return
    thread_name = threading.current_thread().name
    print(f"[Thread-{thread_name}] ", *args, **kwargs)


def regular_print(*args, **kwargs):
    """Custom debug_print function that prefixes output with the current thread ID or name."""
    thread_name = threading.current_thread().name
    print(f"[Thread-{thread_name}] ", *args, **kwargs)


def debug_print_on():
    global DEBUG
    DEBUG = True


def debug_print_off():
    global DEBUG
    DEBUG = False
