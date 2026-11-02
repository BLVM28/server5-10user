"""Download the exact upstream V2 archive; extract validation WAVs only.

Uses the pinned ARM repository's official Google URL. Test/train audio stays
inside the original archive; it is never used for tuning or this regression.
"""
import argparse
import hashlib
import json
import tarfile
import time
import urllib.request
from pathlib import Path

URL = 'https://storage.googleapis.com/download.tensorflow.org/data/speech_commands_v0.02.tar.gz'
SIZE = 2428923189
MD5 = '6b74f3901214cb2c2934e98196829835'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    archive = a.out / 'speech_commands_v0.02.tar.gz'
    partial = archive.with_suffix('.gz.part')
    if not archive.exists():
        start = partial.stat().st_size if partial.exists() else 0
        req = urllib.request.Request(URL, headers={'Range': 'bytes=%d-' % start} if start else {})
        with urllib.request.urlopen(req, timeout=60) as response:
            if start and response.status != 206:
                raise RuntimeError('Server did not honor resume; refusing to append')
            last = time.monotonic()
            with partial.open('ab' if start else 'wb') as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    start += len(chunk)
                    if time.monotonic() - last > 10:
                        print('download %.1f%% (%d/%d)' % (100 * start / SIZE, start, SIZE), flush=True)
                        last = time.monotonic()
        assert partial.stat().st_size == SIZE
        partial.rename(archive)
    md5, sha = hashlib.md5(), hashlib.sha256()
    with archive.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            md5.update(chunk)
            sha.update(chunk)
    assert archive.stat().st_size == SIZE and md5.hexdigest() == MD5, 'Official archive checksum mismatch'
    print('Official archive size and ETag/MD5 verified', flush=True)
    audio = a.out / 'validation'
    audio.mkdir(exist_ok=True)
    # Read list first, then stream the archive once more to avoid unpacking
    # train/test or trusting arbitrary archive member paths.
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        metadata = {}
        for name in ('validation_list.txt', 'testing_list.txt', 'LICENSE', 'README.md'):
            matches = [m for m in members if m.name.lstrip('./') == name]
            if matches:
                data = tar.extractfile(matches[0]).read()
                (a.out / name).write_bytes(data)
                metadata[name] = hashlib.sha256(data).hexdigest()
    valid = set((a.out / 'validation_list.txt').read_text().splitlines())
    testing = set((a.out / 'testing_list.txt').read_text().splitlines())
    assert valid.isdisjoint(testing)
    count = 0
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            name = member.name.removeprefix('./')
            if name not in valid:
                continue
            parts = Path(name).parts
            assert member.isfile() and len(parts) == 2 and '..' not in parts and not Path(name).is_absolute()
            target = audio / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(tar.extractfile(member).read())
            count += 1
    assert count == len(valid)
    report = dict(url=URL, bytes=SIZE, md5=md5.hexdigest(), sha256=sha.hexdigest(),
                  metadata_sha256=metadata, validation_wavs=count,
                  testing_wavs_extracted=0, training_wavs_extracted=0)
    (a.out / 'download.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ALL PASS, %d/%d validation WAVs extracted; test/train not extracted' % (count, count), flush=True)


if __name__ == '__main__':
    main()
