class MusicState:

    def __init__(self):
        self.queue = []
        self.current = None
        self.previous = None
        self.loop = False
        self.autoplay = False
        self.autoplay_seed = None
        self.message = None  # unified control panel message


music_states = {}
