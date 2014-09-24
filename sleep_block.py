from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties import TimeDeltaProperty
from nio.modules.scheduler import Job


@Discoverable(DiscoverableType.block)
class Sleep(Block):

    """ Sleep block.

    Emits the signals passed to it, after a given interval

    Attributes:
        interval (TimeDeltaProperty): Time period of signal emission.

    """

    interval = TimeDeltaProperty(title='Interval', default={'seconds': 1})

    def process_signals(self, signals):
        # After interval, notify these signals
        emit = Job(self.notify_signals, self.interval, False, signals)
