from ctypes import Union


class MusicSrc:
    def __init__(self, title: str, duration, link: str):
        self.duration = duration
        self.title = title
        self.link = link
