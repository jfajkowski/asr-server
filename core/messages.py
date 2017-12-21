MESSAGE_SEPARATOR = b'\n'

class Transcription:
    __slots__ = ('sentence')

    def __init__(self, sentence):
        self.sentence = sentence

    def to_dict(self):
        return {'sentence': self.sentence}
