from typing import List
from config import MAX_WORDS_PER_LINE, LINES_COUNT

def split_text_to_lines(text: str) -> List[str]:
    words = text.strip().split()
    
    if not words:
        return [""] * LINES_COUNT
    
    lines = []
    current_line = []
    
    for word in words:
        if len(current_line) < MAX_WORDS_PER_LINE:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    while len(lines) < LINES_COUNT:
        lines.append("")
    
    return lines[:LINES_COUNT]

def validate_text_length(text: str) -> bool:
    words = text.strip().split()
    max_words = MAX_WORDS_PER_LINE * LINES_COUNT
    return len(words) <= max_words 