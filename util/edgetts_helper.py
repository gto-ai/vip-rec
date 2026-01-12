from pathlib import Path
from datetime import datetime
import uuid
import edge_tts
import subprocess

from config import BASE


class EdgeTTS:
    def __init__(self):
        self.output_folder = Path(BASE, 'cache')
        if self.output_folder.exists() is False:
            self.output_folder.mkdir()
        self.output_folder = str(self.output_folder)

        # self.voice = 'zh-CN-XiaoxiaoNeural'
        self.voice = 'en-SG-LunaNeural'
        # self.voice = 'en-GB-MaisieNeural'
        # self.voice = 'en-US-AnaNeural'
        # self.voice = 'en-HK-YanNeural'
        # self.voice = 'en-US-AriaNeural'

    @classmethod
    async def list_voices(cls):
        voices = await edge_tts.list_voices()
        for voice in voices:
            print(voice['ShortName'], voice['Gender'], voice['Locale'])
        return voices

    async def speak_voices(self):
        voices = await edge_tts.list_voices()
        text = "This is a sample test voice."
        for voice in voices:
            if 'en-' not in voice['ShortName']:
                continue
            print(voice['ShortName'], voice['Gender'], voice['Locale'])
            self.voice = voice['ShortName']
            await self.speak(text, file_name=f"{voice['ShortName']}_{voice['Gender']}")

    async def speak(self, text, **kwargs):
        extension = kwargs.get('extension', '.wav')
        file_name = kwargs.get('file_name', None)
        if file_name is None:
            tmpfile = Path(self.output_folder, f"tts-{datetime.now().date()}_{uuid.uuid4().hex[:8]}{extension}")
        else:
            tmpfile = Path(self.output_folder, f"tts-{file_name}{extension}")

        communicate = edge_tts.Communicate(text, voice=self.voice)
        await communicate.save(str(tmpfile))

        tmp16k = Path(self.output_folder, tmpfile.stem + '_16k.wav')

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(tmpfile),
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(tmp16k)
            ],
            check=True,
        )

        return tmp16k

    async def convert(self, text, audio_path, **kwargs):
        extension = kwargs.get('extension', '.wav')
        file_name = kwargs.get('file_name', None)
        if file_name is None:
            tmpfile = Path(self.output_folder, f"tts-{datetime.now().date()}_{uuid.uuid4().hex[:8]}{extension}")
        else:
            tmpfile = Path(self.output_folder, f"tts-{file_name}{extension}")

        communicate = edge_tts.Communicate(text, voice=self.voice)
        await communicate.save(str(tmpfile))

        tmp16k = Path(audio_path)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(tmpfile),
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(tmp16k)
            ],
            check=True,
        )

        return tmp16k


async def demo_all_voices():
    tts = EdgeTTS()
    await tts.speak_voices()


async def demo():
    tts = EdgeTTS()
    await tts.speak("Hello! Ruofei, Welcome to the air show")


def main():
    import asyncio
    asyncio.run(demo())


if __name__ == "__main__":
    main()
