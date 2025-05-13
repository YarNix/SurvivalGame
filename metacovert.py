import yaml
import sys
from pathlib import Path
from SurvivalGame.components.sprites import SpriteSlice, SpriteSheet
import re
from PIL import Image

def convert(filepath: Path):
    with open(filepath, "r") as f:
        obj: dict = yaml.load(f, yaml.SafeLoader)
        spriteObj = obj['TextureImporter']['spriteSheet']
        sheet = SpriteSheet(list(), dict())
        ani: dict[str, list] = {}
        for sprite in spriteObj['sprites']:
            rect = sprite['rect']
            sheet.sprites.append(SpriteSlice(sprite['name'], list((rect['x'], rect['y'], rect['width'], rect['height'])))) # type: ignore
            nameMatch = re.match(r'([\w]+) *(\d*)$', sprite['name'])
            if not nameMatch:
                continue
            baseName, index = nameMatch.group(1, 2)
            anilist = ani.setdefault(baseName, [])
            try:
                anilist.append((int(index or "0"), sprite['name']))
            except ValueError:
                pass
        for name in list(ani.keys()):
            states = [(indexedName[1], 300.0) for indexedName in sorted(ani[name], key=lambda indexedName: indexedName[0])]
            sheet.states[name] = str(states[0][0]) if len(states) == 1 else states
        print(filepath)
        with open(filepath.with_suffix('.spdt'), 'w+') as of:
            yaml.dump(sheet, of)

if __name__ == "__main__":
    n = len(sys.argv)
    if n <= 1:
        raise ValueError("Missing path to convert")
    for i in range(1, n):
        p = Path(sys.argv[i])
        if p.is_file() and p.suffix == ".meta":
            convert(p)
        elif p.is_dir():
            for sub in p.iterdir():
                if sub.is_file() and sub.suffix == ".meta":
                    convert(sub)