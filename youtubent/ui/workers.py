"""Run slow stuff off the UI thread: run(fn, *args, done=, failed=, progress=).
fn is called as fn(*args, progress=callable). Callbacks always run on the main thread."""
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class _Sig(QObject):
    done = Signal(object)
    failed = Signal(str)
    progress = Signal(float, str)


class _Relay(QObject):
    """Lives in the main thread so callbacks run there (queued connections)."""

    def __init__(self, done, failed, progress):
        super().__init__()
        self._d, self._f, self._p = done, failed, progress

    @Slot(object)
    def on_done(self, r):
        try:
            self._d and self._d(r)
        finally:
            _alive.discard(self.job)

    @Slot(str)
    def on_failed(self, e):
        try:
            self._f and self._f(e)
        finally:
            _alive.discard(self.job)

    @Slot(float, str)
    def on_progress(self, f, m):
        self._p and self._p(f, m)


class Job(QRunnable):
    def __init__(self, fn, *args, relay):
        super().__init__()
        self.fn, self.args, self.relay = fn, args, relay
        self.sig = _Sig()
        self.sig.done.connect(relay.on_done)
        self.sig.failed.connect(relay.on_failed)
        self.sig.progress.connect(relay.on_progress)
        self.setAutoDelete(False)  # we keep it alive until the result is delivered

    def run(self):
        try:
            res = self.fn(*self.args, progress=lambda f, m="": self.sig.progress.emit(float(f), m))
        except Exception as e:
            self.sig.failed.emit(str(e) or e.__class__.__name__)
        else:
            self.sig.done.emit(res)


pool = QThreadPool.globalInstance()
pool.setMaxThreadCount(4)
_alive: set = set()


def run(fn, *args, done=None, failed=None, progress=None) -> Job:
    relay = _Relay(done, failed, progress)
    j = Job(fn, *args, relay=relay)
    relay.job = j
    _alive.add(j)  # released in the relay once the result has been delivered
    pool.start(j)
    return j
