import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DESIGN_DIR = BASE_DIR / "design"
PSD_FILE = DESIGN_DIR / "Rust.psd"
FONT_BOLD = DESIGN_DIR / "a_machinaorto_bold.ttf"
FONT_REGULAR = DESIGN_DIR / "a_machinaorto.ttf"

OUTPUT_SIZE = (660, 440)
MAX_WORDS_PER_LINE = 2
LINES_COUNT = 3

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

TEXT_LAYER_NAMES = ["1", "2", "3"] 