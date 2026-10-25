"""Prepend a quiet 150 ms cue to WAV files which already have a 500 ms pause."""
import argparse
from array import array
import math
from pathlib import Path
import sys
import wave


def add_cue(path: Path):
    with wave.open(str(path), 'rb') as source:
        params = source.getparams()
        if params.sampwidth != 2 or params.comptype != 'NONE':
            raise ValueError(f'Expected 16-bit PCM: {path}')
        speech = source.readframes(params.nframes)
    # Approximately -30 dBFS; short fades prevent clicks at the cue boundaries.
    count = round(params.framerate * 0.15)
    fade = max(1, round(params.framerate * 0.015))
    samples = array('h')
    for i in range(count):
        envelope = min(1, i / fade, (count - 1 - i) / fade)
        value = round(1036 * envelope * math.sin(2 * math.pi * 660 * i / params.framerate))
        samples.extend([value] * params.nchannels)
    if sys.byteorder != 'little':
        samples.byteswap()
    target = path.with_suffix('.cue.tmp')
    try:
        with wave.open(str(target), 'wb') as output:
            output.setparams(params)
            output.writeframes(samples.tobytes() + speech)
        target.replace(path)
    finally:
        target.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    files = sorted(args.directory.glob('*.wav'))
    if not files:
        parser.error('No WAV files found')
    for file in files:
        add_cue(file)
    print(f'Added quiet cue to {len(files)} recordings')
