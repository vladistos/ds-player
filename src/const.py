from wavelink import Track, Player


class Constants:
    FFMPEG_LOCATION = 'src/ffmpeg/ffmpeg.exe'

    FFMPEG_CONFIG = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                     'options': '-vn', "executable": FFMPEG_LOCATION}

    VK_TOKEN = ''


class ErrorTexts:
    NOT_CONNECTED_TO_VOICE = 'Вы не подключены к голосовому каналу'
    GET_VOICE_FAILED = 'Не удалось получить информацию о голосовом канале'
    QUEUE_IS_FULL = 'В очереди уже максимальное колличество треков'


class ReplyTexts:
    DURATION = 'Длительность'
    AUTHOR = 'Автор'

    @staticmethod
    def track_added(track: Track):
        return f'{ReplyTexts.lined(track.title)} добавлен в очередь'

    @staticmethod
    def track_range_added(r: int):
        return f'Добавлено {r} треков'

    @staticmethod
    def volume_changed(val: int):
        return f'Установлена громкость {ReplyTexts.lined(str(val) + "%")}'

    @staticmethod
    def now_playing(player: Player):
        now_playing = player.track.title if player.track is not None else 'ничего'
        return f'{ReplyTexts.NOW_PLAYING} {ReplyTexts.lined(now_playing)}'

    @staticmethod
    def lined(s):
        return f'`{s}`'

    NOW_PLAYING = 'Сейчас играет'
    PAUSED = 'Поставлено на паузу'
    RESUMED = 'Продолжаю воспроизведение'
