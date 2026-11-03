"""Extract a small deterministic training-only engineering set from the local archive."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    data=ROOT.parent/"datasets/speech_commands_v0.02";out=ROOT/"build/train"
    out.mkdir(parents=True,exist_ok=True)
    # Three recordings per command, up to one recording per speaker per word.
    words="yes no up down left right on off stop go bird".split()
    counts={w:0 for w in words};speakers={w:set() for w in words}
    exclude=set((data/"validation_list.txt").read_text().splitlines())|set((data/"testing_list.txt").read_text().splitlines())
    rows=[]
    with tarfile.open(str(data/"speech_commands_v0.02.tar.gz"),"r|gz") as archive:
        for entry in archive:
            rel=entry.name.removeprefix("./")
            parts=rel.split("/")
            if len(parts)!=2 or not rel.endswith(".wav") or rel in exclude or not entry.isfile():continue
            word,name=parts;speaker=name.split("_nohash_")[0]
            if word not in counts or counts[word]>=3 or speaker in speakers[word]:continue
            speakers[word].add(speaker);counts[word]+=1
            target=out/"audio"/word/name
            assert (out/"audio").resolve() in target.resolve().parents
            target.parent.mkdir(parents=True,exist_ok=True)
            audio=archive.extractfile(entry).read();target.write_bytes(audio)
            rows.append({"path":rel,"sha256":hashlib.sha256(audio).hexdigest()})
            if min(counts.values())==3:break
    assert len(rows)==33
    (out/"selection.json").write_text(json.dumps(rows,indent=2)+"\n")
    print("TRAINING SELECTION PASS",len(rows))
if __name__=="__main__":main()
