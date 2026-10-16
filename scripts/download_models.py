import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
from huggingface_hub import snapshot_download

# IndicTrans2: skip the duplicate .bin file, the .safetensors weights are enough
for repo in ["ai4bharat/indictrans2-indic-en-dist-200M",
             "ai4bharat/indictrans2-en-indic-dist-200M"]:
    print("Downloading", repo)
    snapshot_download(repo, ignore_patterns=["*.bin"])

# Whisper needs its model.bin, so download this one in full
print("Downloading Systran/faster-whisper-small")
snapshot_download("Systran/faster-whisper-small")
print("All done")