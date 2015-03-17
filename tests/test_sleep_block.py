import time
from ..sleep_block import Sleep
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.threading import Event
from nio.common.signal.base import Signal


class SleepEvent(Sleep):

    def __init__(self, event):
        super().__init__()
        self.event = event

    def notify_signals(self, signals, output_id='default'):
        super().notify_signals(signals, output_id)
        self.event.set()


class TestSleep(NIOBlockTestCase):

    def test_sleep_block(self):
        e = Event()
        blk = SleepEvent(e)
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 1}
        })
        blk.start()
        signals = [Signal({'name': 'signal1'}),
                   Signal({'name': 'signal2'})]
        start = time.time()
        blk.process_signals(signals)
        self.assert_num_signals_notified(0)
        e.wait()
        end = time.time()
        self.assert_num_signals_notified(2)
        self.assertTrue(1.0 < end - start < 1.1)
        blk.stop()
