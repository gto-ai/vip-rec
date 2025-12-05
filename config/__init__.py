import os
from pathlib import Path
import pyprojroot
from dotenv import find_dotenv, load_dotenv

HOME: Path = Path.home()
BASE: Path = pyprojroot.find_root(pyprojroot.has_dir("config"))
WORKSPACE: Path = BASE.parent.parent
ENV = "dev"

load_dotenv(Path(BASE, ".env"))