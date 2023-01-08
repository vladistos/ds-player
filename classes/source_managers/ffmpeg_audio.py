import io
import shlex
import subprocess
import threading
from abc import ABC
from typing import Union, Any, Optional, IO

import ffmpeg
from discord import AudioSource, ClientException
from discord.opus import Encoder as OpusEncoder
from wavelink.utils import MISSING

from classes.source_managers.audiofilters import AudioFilter, FilterManager
from src.const import Constants


class FFMPEGAudio(AudioSource, ABC):

    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = "ffmpeg",
        args: Any,
        **subprocess_kwargs: Any,
    ):
        self.piping = subprocess_kwargs.get("stdin") == subprocess.PIPE
        if self.piping and isinstance(source, str):
            raise TypeError("parameter conflict: 'source' parameter cannot be a string when piping to stdin")

        self.source = source
        self.args = [executable, *args]
        self.kwargs = {"stdout": subprocess.PIPE}
        self.kwargs.update(subprocess_kwargs)
        self._init()

    def _init(self):
        self._process: subprocess.Popen = self._spawn_process(self.args, **self.kwargs)
        self._stdout: IO[bytes] = self._process.stdout  # type: ignore
        self._stdin: Optional[IO[bytes]] = None
        self._pipe_thread: Optional[threading.Thread] = None

        if self.piping:
            n = f"popen-stdin-writer:{id(self):#x}"
            self._stdin = self._process.stdin
            self._pipe_thread = threading.Thread(target=self._pipe_writer, args=(self.source,), daemon=True, name=n)
            self._pipe_thread.start()

    @staticmethod
    def _spawn_process(args: Any, **subprocess_kwargs: Any) -> subprocess.Popen:
        try:
            process = subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW, **subprocess_kwargs)
        except FileNotFoundError:
            executable = args.partition(" ")[0] if isinstance(args, str) else args[0]
            raise ClientException(f"{executable} was not found.") from None
        except subprocess.SubprocessError as exc:
            raise ClientException(f"Popen failed: {exc.__class__.__name__}: {exc}") from exc
        else:
            return process

    def _kill_process(self) -> None:
        proc = self._process
        if proc is MISSING:
            return

    def _pipe_writer(self, source: io.BufferedIOBase) -> None:
        while self._process:
            # arbitrarily large read size
            data = source.read(8192)
            if not data:
                self._process.terminate()
                return
            try:
                self._stdin.write(data)
            except Exception:
                # at this point the source data is either exhausted or the process is fubar
                self._process.terminate()
                return

    def cleanup(self) -> None:
        self._kill_process()
        self._process = self._stdout = self._stdin = MISSING


class FFMPEGPCMAudio(FFMPEGAudio):

    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = "ffmpeg",
        frame_weight: float = 1,
        offset: float = 0,
        pipe: bool = False,
        stderr: Optional[IO[str]] = None,
        before_options: Optional[str] = None,
        options: Optional[str] = None,
        additional_args: list[str] = None
    ) -> None:
        self.frame_weight = frame_weight
        args = []
        subprocess_kwargs = {
            "stdin": subprocess.PIPE if pipe else subprocess.DEVNULL,
            "stderr": stderr,
        }

        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))

        self.offset = offset
        args.extend(('-ss', str(offset)))

        args.append("-i")
        args.append("-" if pipe else source)
        args.extend(("-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "warning"))
        args.extend(additional_args or [])

        if isinstance(options, str):
            args.extend(shlex.split(options))

        args.append("pipe:1")

        super().__init__(source, executable=executable, args=args, **subprocess_kwargs)

    def skip_frames(self, frames):
        self._stdout.read(OpusEncoder.FRAME_SIZE * frames)
        self.offset += frames

    def read(self, frames=1) -> bytes:
        ret = self._stdout.read(OpusEncoder.FRAME_SIZE * frames)
        self.offset += frames * self.frame_weight * 0.02
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b""
        return ret

    def is_opus(self) -> bool:
        return False


class AudioMeta:
    def __init__(self, title: str, photo: str = None, author: str = None, duration: int = None):
        self.photo = photo
        self.author = author
        self.duration = duration
        self.title = title


class PlayableAudio(AudioSource):

    def __init__(self, source: Union[str, io.BufferedIOBase], filters: list[AudioFilter] = None,
                 meta_info: AudioMeta = None, **kwargs,):
        self.meta_info = meta_info
        filters = filters or []
        self._filter_manager = FilterManager(*filters)
        self.source = source
        kwargs.update(**Constants.FFMPEG_CONFIG)
        self._init_kwargs = kwargs
        self._ffmpeg_audio = None

    @property
    def ffmpeg_audio(self):
        return self._ffmpeg_audio or self._get_ffmpeg_audio()

    def _get_ffmpeg_audio(self, offset=0.0) -> FFMPEGPCMAudio:
        print(self._filter_manager.speed)
        return FFMPEGPCMAudio(source=self.source,
                              additional_args=self._filter_manager.filter_args,
                              offset=offset,
                              frame_weight=self._filter_manager.speed,
                              **self._init_kwargs)

    def cleanup(self) -> None:
        if self._ffmpeg_audio:
            self._ffmpeg_audio.cleanup()

    def seek_to(self, seconds: float):
        self._ffmpeg_audio = self._get_ffmpeg_audio(offset=seconds)

    def set_filters(self, filters: list[AudioFilter]):
        self._filter_manager = FilterManager(*filters)
        offset = self._ffmpeg_audio.offset if self._ffmpeg_audio else 0
        self._ffmpeg_audio = self._get_ffmpeg_audio(offset=offset)

    def read(self) -> bytes:
        return self.ffmpeg_audio.read()
