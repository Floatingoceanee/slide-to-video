"""
Subtitle proofreading module.

Compares Whisper-generated SRT files with the original script.txt
to correct obvious errors (e.g., proper nouns) while preserving
the original timestamp structure.
"""

import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def extract_script_text(script_path: str) -> str:
    """
    Extract pure text content from script.txt.

    - Ignores NEWSLIDE markers
    - Ignores === and subsequent config content (#delay, etc.)
    - Returns cleaned pure text

    Args:
        script_path: Path to the script.txt file

    Returns:
        Cleaned text content
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by NEWSLIDE marker and process each section
    sections = content.split('NEWSLIDE')

    cleaned_sections = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Remove === and everything after (config section)
        if '===' in section:
            section = section.split('===')[0].strip()

        if section:
            cleaned_sections.append(section)

    # Join all sections with space
    return ' '.join(cleaned_sections)


def extract_srt_text(srt_path: str) -> List[Dict]:
    """
    Extract text content from SRT file.

    - Ignores timeline lines
    - Returns [{index, text}, ...] format

    Args:
        srt_path: Path to the SRT file

    Returns:
        List of dicts with index and text for each subtitle segment
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse SRT segments
    # Format: index\nstart --> end\ntext\n\n
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([^\n]+(?:\n[^\n]+\n)?)'
    matches = re.findall(pattern, content)

    segments = []
    for match in matches:
        index = int(match[0])
        text = match[3].strip()
        segments.append({
            'index': index,
            'text': text
        })

    return segments


def extract_script_vocabulary(script_text: str) -> set:
    """
    Extract vocabulary (words) from script text.

    Args:
        script_text: The cleaned script text

    Returns:
        Set of words from the script
    """
    # Simple word extraction - alphanumeric words
    words = re.findall(r'\b[\w-]+\b', script_text.lower())
    return set(words)


def find_best_match(word: str, vocabulary: set, threshold: float = 0.8) -> Optional[str]:
    """
    Find the best matching word from vocabulary using simple similarity.

    Args:
        word: The word to match
        vocabulary: Set of vocabulary words
        threshold: Minimum similarity ratio (0-1)

    Returns:
        Best matching word or None if no good match found
    """
    from difflib import SequenceMatcher

    word_lower = word.lower()
    best_match = None
    best_ratio = 0

    for vocab_word in vocabulary:
        ratio = SequenceMatcher(None, word_lower, vocab_word.lower()).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = vocab_word

    return best_match


def proofread_segment_text(srt_text: str, script_text: str, vocabulary: set) -> str:
    """
    Proofread a single subtitle segment's text.

    - Compares words with script vocabulary
    - Replaces obvious errors with script words
    - Preserves original structure and punctuation

    Args:
        srt_text: The SRT segment text
        script_text: The full script text (for context)
        vocabulary: Set of vocabulary words from script

    Returns:
        Corrected text
    """
    # Split text into words while preserving structure
    # This regex captures words and separators (spaces, punctuation)
    tokens = re.findall(r'[\w-]+|[^\w-]+', srt_text)

    corrected_tokens = []
    for token in tokens:
        # Only process word tokens (alphanumeric)
        if re.match(r'^[\w-]+$', token):
            # Check if word exists in vocabulary (case-insensitive)
            token_lower = token.lower()
            if token_lower not in vocabulary:
                # Try to find a better match
                best_match = find_best_match(token, vocabulary)
                if best_match:
                    # Preserve original case pattern
                    if token[0].isupper():
                        corrected_token = best_match.capitalize()
                    elif token.isupper():
                        corrected_token = best_match.upper()
                    else:
                        corrected_token = best_match
                    corrected_tokens.append(corrected_token)
                    logger.debug(f"Corrected '{token}' -> '{corrected_token}'")
                else:
                    corrected_tokens.append(token)
            else:
                corrected_tokens.append(token)
        else:
            corrected_tokens.append(token)

    return ''.join(corrected_tokens)


def proofread_srt(srt_path: str, script_path: str, output_path: str) -> str:
    """
    Proofread SRT file using script.txt as reference.

    - Matches SRT text with script text
    - Uses script.txt text to replace obvious errors in SRT
    - Preserves SRT timeline structure
    - Outputs subtitles_merged_proofread.srt

    Args:
        srt_path: Path to the input SRT file
        script_path: Path to the script.txt reference file
        output_path: Path for the output proofread SRT file

    Returns:
        Path to the output file
    """
    logger.info(f"Proofreading SRT: {srt_path}")
    logger.info(f"Using script reference: {script_path}")

    # Extract script text and vocabulary
    script_text = extract_script_text(script_path)
    vocabulary = extract_script_vocabulary(script_text)
    logger.info(f"Extracted {len(vocabulary)} unique words from script")

    # Read original SRT
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # Parse SRT segments with full details
    # Pattern captures: index, start_time, end_time, text (possibly multiline)
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([^\n]+(?:\n(?!\d+\n)[^\n]+)*)'

    def replace_segment(match):
        index = match.group(1)
        start_time = match.group(2)
        end_time = match.group(3)
        text = match.group(4).strip()

        # Proofread the text
        corrected_text = proofread_segment_text(text, script_text, vocabulary)

        return f"{index}\n{start_time} --> {end_time}\n{corrected_text}\n"

    # Replace each segment
    proofread_content = re.sub(pattern, replace_segment, srt_content)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(proofread_content)

    logger.info(f"Proofread SRT saved to: {output_path}")
    return output_path


def compare_srt_texts(original_path: str, proofread_path: str) -> List[Dict]:
    """
    Compare original and proofread SRT files to show changes.

    Args:
        original_path: Path to original SRT
        proofread_path: Path to proofread SRT

    Returns:
        List of changes with index, original text, and corrected text
    """
    original_segments = extract_srt_text(original_path)
    proofread_segments = extract_srt_text(proofread_path)

    changes = []
    for orig, proof in zip(original_segments, proofread_segments):
        if orig['text'] != proof['text']:
            changes.append({
                'index': orig['index'],
                'original': orig['text'],
                'corrected': proof['text']
            })

    return changes
