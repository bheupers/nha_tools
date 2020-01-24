import os
import hashlib


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


for root, subdirs, files in os.walk('.'):
    for file in files:
        fullpath = os.path.join(root, file)
        md5sum = md5(fullpath)
        print(f"{fullpath}:  {md5sum}")

