import logging
import re
import subprocess
from threading import Thread


class FileDecoder:
    def __init__(self):
        self._baseline = []
        self._baseline.append(subprocess.Popen(['./file-decoder',
                                                '--config=model/conf/online_decoding.conf',
                                                'model/graph/HCLG.fst',
                                                'model/graph/words.txt',
                                                'scp:-',
                                                'ark:-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-lmrescore',
                                                '--lm-scale=-1.0',
                                                'ark:-',
                                                '/home/jfajkowski/Projects/kaldi/tools/openfst/bin/fstproject --project_output=true model/base.fst |',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-lmrescore',
                                                '--lm-scale=1.0',
                                                'ark:-',
                                                '/home/jfajkowski/Projects/kaldi/tools/openfst/bin/fstproject --project_output=true model/rescore.fst |',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-scale',
                                                '--inv-acoustic-scale=17',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-add-penalty',
                                                '--word-ins-penalty=1.0',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-best-path',
                                                '--word-symbol-table=model/graph/words.txt',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stderr=subprocess.PIPE))

    def decode(self, wav_path):
        self._write(wav_path)
        transcription = self._read(wav_path)
        return transcription

    def _write(self, wav_path):
        self._baseline[0].stdin.write('{}\t{}\n'.format(wav_path, wav_path).encode('UTF-8'))
        self._baseline[0].stdin.flush()

    def _read(self, wav_path):
        while True:
            result = self._baseline[-1].stderr.readline().decode('UTF-8')
            match = re.findall(r'^{} (.+)'.format(wav_path), result)
            if match:
                return match[0].strip()


class StreamDecoder:
    def __init__(self, callback):
        self._baseline = []
        self._baseline.append(subprocess.Popen(['./stream-decoder',
                                                '--config=model/conf/online_decoding.conf',
                                                'model/graph/HCLG.fst',
                                                'model/graph/words.txt',
                                                '-',
                                                'ark:-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-lmrescore',
                                                '--lm-scale=-1.0',
                                                'ark:-',
                                                '/home/jfajkowski/Projects/kaldi/tools/openfst/bin/fstproject --project_output=true model/base.fst |',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-lmrescore',
                                                '--lm-scale=1.0',
                                                'ark:-',
                                                '/home/jfajkowski/Projects/kaldi/tools/openfst/bin/fstproject --project_output=true model/rescore.fst |',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-scale',
                                                '--inv-acoustic-scale=17',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-add-penalty',
                                                '--word-ins-penalty=1.0',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stdout=subprocess.PIPE))
        self._baseline.append(subprocess.Popen(['/home/jfajkowski/Projects/kaldi/src/latbin/lattice-best-path',
                                                '--word-symbol-table=model/graph/words.txt',
                                                'ark:-',
                                                'ark:-'], stdin=self._baseline[-1].stdout, stderr=subprocess.PIPE))

        self._decoding = True
        self._callback = callback
        self._thread = Thread(target=self._read)
        self._thread.start()

    def terminate(self):
        for process in self._baseline:
            process.terminate()

    def decode(self, frames):
        self._write(frames)

    def _write(self, frames):
        self._baseline[0].stdin.write(frames)
        self._baseline[0].stdin.flush()

    def _read(self):
        while self._decoding:
            result = self._baseline[-1].stderr.readline().decode('UTF-8').strip()
            if re.match('\d+ .+', result):
                result = result.lstrip('0123456789 ')
                logging.info('Decoded: {}'.format(result))
                self._callback(result)
            else:
                pass
