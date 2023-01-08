import random
from typing import Optional, Callable, Any

from discord import VoiceClient, Client, abc

from classes.source_managers.audiofilters import AudioFilter
from classes.source_managers.ffmpeg_audio import PlayableAudio


class Queue:
    def __init__(self):
        self.track_list: list[PlayableAudio] = []
        self.position = -1

    @property
    def count(self):
        return len(self.track_list)

    def next(self):
        return self.increment_pos(1)

    def prev(self):
        return self.increment_pos(-1)

    def increment_pos(self, dif: int):
        self.position = max(min(self.position + dif, self.count-1), 0)
        if self.count <= self.position or self.position < 0:
            return None
        return self.track_list[self.position]


class FFMPEGPlayer(VoiceClient):
    def __init__(self, client: Client, channel: abc.Connectable):
        super().__init__(client, channel)
        self.filters: list[AudioFilter] = []
        self.on_track_ended_callback = None
        self.queue: Queue = Queue()
        self.view = None

    def set_filters(self, *filters: AudioFilter):
        self.filters = list(filters)
        source = self.source
        if source and isinstance(source, PlayableAudio):
            source.set_filters(self.filters)

    @property
    def source(self) -> Optional[PlayableAudio]:
        return super().source

    def next_track(self):
        track = self.queue.next()
        if track:
            self.play(track)

    def prev_track(self):
        track = self.queue.prev()
        if track:
            self.play(track)

    def on_track_ended(self, error):
        print(error)
        self.next_track()
        if self.on_track_ended_callback:
            self.on_track_ended_callback()

    def add_to_queue(self, *tracks, start_playing=False):
        self.queue.track_list.extend(list(tracks))
        if start_playing and not self.is_playing():
            self.next_track()

    def play_or_pause(self):
        if self.is_paused():
            self.resume()
        else:
            self.pause()
        return self.is_paused()

    def shuffle(self):
        random.shuffle(self.queue.track_list)

    def play(self, track: PlayableAudio, **kwargs) -> None:
        track.set_filters(self.filters)
        track.seek_to(0)
        if self.is_playing():
            self.pause()
            self.source.cleanup()
        super().play(track, after=self.on_track_ended)
