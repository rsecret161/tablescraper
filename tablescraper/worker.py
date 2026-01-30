import threading


def run_background(target, args=(), on_complete=None, on_error=None):
    """Run `target(*args)` in a daemon thread and callbacks on completion/error.

    Callbacks are called in the worker thread; GUI callers should use `root.after`
    to schedule UI updates on the main thread.
    """

    def wrapped():
        try:
            res = target(*args)
            if on_complete:
                try:
                    on_complete(res)
                except Exception:
                    # Callbacks shouldn't crash worker thread; swallow exceptions
                    pass
        except Exception as e:
            if on_error:
                try:
                    on_error(e)
                except Exception:
                    pass

    thr = threading.Thread(target=wrapped, daemon=True)
    thr.start()
    return thr
