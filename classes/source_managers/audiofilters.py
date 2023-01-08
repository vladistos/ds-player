from abc import abstractmethod, ABCMeta


class AudioFilter(metaclass=ABCMeta):
    @property
    def str(self) -> str:
        raise NotImplementedError

    @property
    def id(self) -> int:
        raise NotImplementedError

    def __eq__(self, other):
        if other.id == self.id:
            return True
        return False

    def __str__(self):
        return self.str


class InOutGainFilter(AudioFilter, metaclass=ABCMeta):
    def __init__(self, in_gain: float = None, out_gain: float = None):
        self.in_gain = in_gain or 1
        self.out_gain = out_gain or 1

    @property
    def inout_gain_str(self) -> str:
        return f'in_gain={self.in_gain}:out_gain={self.out_gain}'


class SpeedFilter(AudioFilter, metaclass=ABCMeta):
    @property
    def speed(self) -> float:
        raise NotImplementedError


class ReverseFilter(AudioFilter):
    @property
    def id(self) -> int:
        return 1

    @property
    def str(self) -> str:
        return 'areverse'


class DelayFilter(InOutGainFilter):
    @property
    def id(self) -> int:
        return 2

    def __init__(self, in_gain: float = None, out_gain: float = None, time_intervals: list[int] = None,
                 decays: list[int] = None):
        super().__init__(in_gain, out_gain)
        self.time_intervals = time_intervals or [1000]
        self.time_intervals = [str(i) for i in self.time_intervals]
        self.decays = decays or [0.5]
        self.decays = [str(i) for i in self.decays]

    @property
    def str(self) -> str:
        return f'aecho={self.inout_gain_str}:delays={"|".join(self.time_intervals)}' \
               f':decays={"|".join(self.decays)}'


class TempoFilter(SpeedFilter):
    @property
    def id(self) -> int:
        return 3

    def __init__(self, tempo: float):
        self.tempo = tempo

    @property
    def speed(self) -> float:
        return max(min(float(self.tempo), 10), 0)

    @property
    def str(self) -> str:
        return f'asetrate=44100*{self.tempo}'


class VolumeFilter(AudioFilter):

    def __init__(self, volume=5):
        self.volume = float(volume)

    @property
    def str(self) -> str:
        return f'volume={self.volume}'

    @property
    def id(self) -> int:
        return 4


class ReverbFilter(AudioFilter):

    @property
    def str(self) -> str:
        return 'aecho=1.0:0.7:20:0.5'

    @property
    def id(self) -> int:
        return 5


class FilterManager:
    def __init__(self, *filters: AudioFilter):
        self._filters = list(filters)
        self._speed, self._args = self._manage_filters()

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def filter_args(self) -> list[str]:
        return self._args

    def _manage_filters(self) -> (float, list[str]):
        speed = 1.0
        filter_count = len(self._filters)
        args = ['-af'] if filter_count > 0 else []
        s = ''
        for i, f in enumerate(self._filters):
            if isinstance(f, SpeedFilter):
                speed *= f.speed
            s += (f.str + (',' if i != filter_count - 1 else ''))
        if len(s) > 0:
            args.append(s)
        return speed, args
