import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perfumestore.settings")

import django

django.setup()

from store.models import Perfume

ROOT = BASE_DIR / "store" / "static" / "store" / "img" / "generated"
ROOT.mkdir(parents=True, exist_ok=True)
FIXTURE = BASE_DIR / "store" / "fixtures" / "initial_perfumes.json"

palettes = [
    ("f7d7c7", "b85c50", "6b2d2d"),
    ("f4d7a8", "c48d3f", "5c3a23"),
    ("dfeec2", "7aa76a", "2b552b"),
    ("d9d3ff", "6d67c9", "2d2b62"),
    ("f5d9ef", "d96fb5", "6c2d5c"),
    ("d8f3ff", "5aa9d6", "214e70"),
    ("f1d7b5", "d28b4d", "513521"),
    ("f0f0d6", "d2c76a", "625d28"),
    ("d8f3ee", "5bb9a8", "1c4f46"),
    ("ffe3d7", "ea9d6d", "6c3d29"),
]

with FIXTURE.open("r", encoding="utf-8") as fh:
    data = json.load(fh)

for index, item in enumerate(data, start=1):
    name = item["fields"]["name"]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"perfume-{index}"
    colors = palettes[(index - 1) % len(palettes)]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000" viewBox="0 0 800 1000">'
        '<defs>'
        '<linearGradient id="bg{0}" x1="0" x2="1" y1="0" y2="1">'
        '<stop offset="0%" stop-color="#{1}"/>'
        '<stop offset="100%" stop-color="#{2}"/>'
        '</linearGradient>'
        '<linearGradient id="glass{0}" x1="0" x2="0" y1="0" y2="1">'
        '<stop offset="0%" stop-color="rgba(255,255,255,0.85)"/>'
        '<stop offset="100%" stop-color="rgba(255,255,255,0.2)"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="800" height="1000" fill="url(#bg{0})"/>'
        '<circle cx="400" cy="180" r="130" fill="rgba(255,255,255,0.18)"/>'
        '<rect x="295" y="220" width="210" height="510" rx="36" fill="#{3}" opacity="0.75"/>'
        '<rect x="318" y="260" width="164" height="420" rx="30" fill="url(#glass{0})"/>'
        '<rect x="330" y="210" width="140" height="70" rx="18" fill="#f5efe8" opacity="0.9"/>'
        '<rect x="350" y="135" width="100" height="90" rx="12" fill="#e7d7c7" opacity="0.7"/>'
        '<rect x="330" y="700" width="140" height="25" rx="12" fill="#f5efe8" opacity="0.8"/>'
        '<text x="400" y="820" text-anchor="middle" font-size="34" font-family="Segoe UI, Arial" fill="#fffaf5" font-weight="700">{4}</text>'
        '<text x="400" y="870" text-anchor="middle" font-size="20" font-family="Segoe UI, Arial" fill="#fffaf5" opacity="0.9">luxury fragrance</text>'
        '</svg>'
    ).format(index, colors[0], colors[1], colors[2], name)
    file_path = ROOT / f"{slug}.svg"
    file_path.write_text(svg, encoding="utf-8")
    item["fields"]["image"] = f"img/generated/{slug}.svg"

with FIXTURE.open("w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

Perfume.objects.all().delete()
subprocess.run([sys.executable, "manage.py", "loaddata", "initial_perfumes"], cwd=str(BASE_DIR), check=True)

unique_images = {p.image for p in Perfume.objects.all()}
print(f"unique_images={len(unique_images)}")
print([(p.name, p.image) for p in Perfume.objects.order_by("id")[:5]])
