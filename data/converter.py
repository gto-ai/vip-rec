from pathlib import Path
from config import BASE
from util.edgetts_helper import EdgeTTS
import asyncio
import re
import json
import shutil


class Converter:
    tts = EdgeTTS()
    pattern = re.compile(
        r"^(?:\[action:\s*(?P<action>[^\]]+)\]\s*)?(?P<content>.+)$"
    )

    @classmethod
    def convert(cls):

        data_dir = Path(BASE, "data")

        dict_info = {}

        for file_path in data_dir.glob("*.md"):
            folder = Path(BASE, 'data', file_path.stem)
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
            info = cls.parse_article(file_path)
            dict_info[file_path.stem] = info

        out_path = Path(BASE, "data", "articles.json")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(dict_info, f, ensure_ascii=False, indent=2)

        return dict_info

    @classmethod
    def parse_article(cls, file_path):
        info = []

        with file_path.open("r", encoding="utf-8") as f:
            idx = 0
            for line in f:
                line = line.rstrip("\n")
                m = cls.pattern.match(line)
                if m is None:
                    continue
                content = m.group("content")
                if content is not None:
                    audio_path = Path(BASE, 'data', file_path.stem, f'{file_path.stem}_{idx:03}.wav')
                    asyncio.run(cls.tts.convert(content, audio_path))
                    idx += 1

                action = m.group("action")
                if action is not None:
                    info.append({'action': action, 'audio': str(audio_path)})
                else:
                    info.append({'action': '', 'audio': str(audio_path)})

            return info


def main():
    dict_info = Converter.convert()
    print(dict_info)

if __name__ == "__main__":
    main()
