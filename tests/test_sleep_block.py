from time import time as _time
from unittest.mock import MagicMock, patch
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.persistence.default import Persistence
from nio.modules.threading import Event
from nio.common.signal.base import Signal
from ..sleep_block import Sleep


class SleepEvent(Sleep):

    def __init__(self, event):
        super().__init__()
        self.event = event

    def notify_signals(self, signals, output_id='default'):
        super().notify_signals(signals, output_id)
        self.event.set()


class TestSleep(NIOBlockTestCase):

    def get_test_modules(self):
        return super().get_test_modules() + ['persistence']

    def get_module_config_persistence(self):
        return {'persistence': 'default'}

    def test_sleep_block(self):
        e = Event()
        blk = SleepEvent(e)
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 0.1}
        })
        blk.start()
        signals = [Signal({'name': 'signal1'}),
                   Signal({'name': 'signal2'})]
        start = _time()
        blk.process_signals(signals)
        # check that signals are not notified immediately
        # but are notified after a short wait
        self.assert_num_signals_notified(0)
        self.assertTrue(e.wait(2))
        self.assert_num_signals_notified(2)
        blk.stop()

    def test_persist_save(self):
        blk = Sleep()
        self.configure_block(blk, {
            'log_level': 'DEBUG',
            'interval': {'seconds': 10}
        })
        blk.persistence.store = MagicMock()
        blk.persistence.save = MagicMock()
        blk.start()
        signals_a = [Signal({'name': 'signal1'}),
                     Signal({'name': 'signal2'})]
        signals_b = [Signal({'name': 'signal3'}),
                     Signal({'name': 'signal4'})]

        def assert_persistence(store_count, save_count):
            self.assertEqual(blk.persistence.store.call_count, store_count)
            self.assertEqual(blk.persistence.save.call_count, save_count)
            self.assertEqual(blk.persistence.store.call_args[0][0],
                            'signals')
            self.assertEqual(blk.persistence.store.call_args[0][1],
                            blk._signals)

        # process some signals
        blk.process_signals(signals_a)
        # process some more signals
        blk.process_signals(signals_b)
        # stop the block and save persistence
        blk.stop()
        assert_persistence(1, 1)

        # the block should have stopped before any signals were notified
        self.assert_num_signals_notified(0)
        # assert that two groups of signals were saved
        self.assertEqual(len(blk._signals), 2)
        # assert that each group has two signals
        self.assertEqual(len(blk._signals[0][1]), 2)
        self.assertEqual(len(blk._signals[1][1]), 2)
        # assert that the second set of signals has a later time than the first
        self.assertTrue(blk._signals[0][0] < blk._signals[1][0])

    def test_persist_load(self):
        ctime = _time()
        e = Event()
        blk = SleepEvent(e)
        signals1 = [Signal()]
        signals2 = [Signal(), Signal()]
        signals = [(ctime, signals1), (ctime + 1, signals2)]
        with patch('nio.common.block.base.Persistence') as persist:
            persist.return_value.load.return_value = signals
            persist.return_value.has_key.side_effect = \
                lambda key: key in ["signals"]
            self.configure_block(blk, {
                'log_level': 'DEBUG',
                'interval': {'seconds': 1}
            })
        blk.start()
        # all signals load but only signals2 are put back into _signals
        self.assertEqual(blk._load_signals, signals)
        self.assertEqual(len(blk._signals), 1)
        self.assertEqual(len(blk._signals[0][1]), 2)
        self.assert_num_signals_notified(0)
        # wait for signals2 to be notified
        e.wait(2)
        self.assert_num_signals_notified(2)
        # then when the block stops, no more signals are stored
        blk.stop()
        self.assertEqual(len(blk._signals), 0)

    def test_persist_load_nothing(self):
        e = Event()
        blk = SleepEvent(e)
        with patch('nio.modules.persistence.Persistence.load'):
            self.configure_block(blk, {
                'log_level': 'DEBUG',
                'interval': {'seconds': 10}
            })
        blk.start()
        self.assertEqual(blk._load_signals, [])
        blk.stop()
