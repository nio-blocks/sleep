from datetime import timedelta
from time import time as _time
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties import TimeDeltaProperty
from nio.modules.scheduler import Job
from nio.modules.threading import Lock


@Discoverable(DiscoverableType.block)
class Sleep(Block):

    """ Sleep block.

    Emits the signals passed to it, after a given interval

    Attributes:
        interval (TimeDeltaProperty): Time period of signal emission.

    """

    interval = TimeDeltaProperty(title='Interval', default={'seconds': 1})

    def __init__(self):
        super().__init__()
        self._signals = []
        self._signals_lock = Lock()

    def configure(self, context):
        super().configure(context)
        self._load_signals = self.persistence.load('signals') or []

    def start(self):
        super().start()
        self._schedule_persistence_sleeps()

    def stop(self):
        super().stop()
        self._store_signals(_time())
        self.persistence.save()

    def process_signals(self, signals):
        # After interval, notify these signals
        emit = Job(self.notify_signals, self.interval, False, signals)
        self._store_signals(_time() + self.interval.total_seconds(), signals)

    def _schedule_persistence_sleeps(self):
        """ Schedule emit jobs for signals loaded from persistence """
        ctime = _time()
        for (time, signals) in self._load_signals:
            # get time to go before the signals should be notified
            dtime = time - ctime
            if dtime > 0 and signals:
                dtime = timedelta(seconds=dtime)
                Job(self.notify_signals, dtime, False, signals)
                self._store_signals(time, signals)

    def _store_signals(self, notify_time, signals=None):
        """ Add new signals and trim old ones before storing """
        with self._signals_lock:
            if signals:
                self._signals.append((notify_time, signals))
            self._signals = self._trim_old_signals(_time(), self._signals)
            self.persistence.store('signals', self._signals)

    def _trim_old_signals(self, ctime, signals):
        """ Remove signals from `signals` older than `ctime` """
        return [(t, s) for (t, s) in self._signals if ctime <= t]
