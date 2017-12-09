class Manager:
    def __init__(self, keep_order=False):
        self._decoders = []
        self._recorders = []

    def initialize(self):
        for decoder in self._decoders:
            decoder.initialize()

    def register_decoder(self, decoder):
        self._decoders.append(decoder)

    def register_recorder(self, recorder):
        recorder.register_on_file_saved_listener(self._assign_recording)
        self._recorders.append(recorder)

    def _assign_recording(self, filename):
        least_loaded_decoder = min(self._decoders, key=lambda x: x.queue_length)
        least_loaded_decoder.decode(filename)
