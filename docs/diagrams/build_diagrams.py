"""Genera los 31 diagramas Mermaid (.mmd) y sus PNGs estrictamente B&N."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from PIL import Image

from diagrams_global_and_m1_m2 import DIAGRAMS_PART_1
from diagrams_m3_and_m4 import DIAGRAMS_PART_2

BASE_DIR = Path("/home/molano/sajona-core/docs/diagrams")
SRC_DIR = BASE_DIR / "src"
PNG_DIR = BASE_DIR / "png"
CONFIG_FILE = BASE_DIR / "mermaid_bw_config.json"
PUPPETEER_FILE = BASE_DIR / "puppeteer_config.json"


def render_one(item: tuple[str, str]) -> str:
    name, code = item
    mmd_path = SRC_DIR / f"{name}.mmd"
    png_path = PNG_DIR / f"{name}.png"
    mmd_path.write_text(code.strip() + "\n", encoding="utf-8")

    subprocess.run(
        [
            "mmdc",
            "-i",
            str(mmd_path),
            "-o",
            str(png_path),
            "-c",
            str(CONFIG_FILE),
            "-p",
            str(PUPPETEER_FILE),
            "-s",
            "3",
            "-b",
            "white",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    with Image.open(png_path) as im:
        bw = im.convert("L").convert("RGB")
        bw.save(png_path)
        size = bw.size
    return f"{name}.png {size}"


def main() -> None:
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    all_diagrams = {**DIAGRAMS_PART_1, **DIAGRAMS_PART_2}
    print(f"Generando y renderizando {len(all_diagrams)} diagramas monocromáticos...")

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(render_one, all_diagrams.items()))

    for r in results:
        print("OK:", r)
    print(f"Total renderizados: {len(results)}")


if __name__ == "__main__":
    main()
