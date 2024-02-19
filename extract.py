from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import IO, Any


class NougatExtractor:
    def __init__(self, batch_size: int = 4, min_words: int = 25):
        """
        Extract text from a pdf file using nougat-ocr.

        Args:
            batch_size (int, optional): batch size for nougat-ocr. Defaults to 4.
            min_words (int, optional): minimum number of words for a paragraph to be included in the output. Defaults to 25.
        """
        self.batch_size = batch_size
        self.min_words = min_words

    # TODO: options for capturing the output + piping it to a file
    def extract_pdf_text(self, path: Path, log: IO[Any] | int | None = None, cache: bool = True) -> str:
        """
        extract text from a pdf file using nougat-ocr

        Args:
            path (Path): path to the pdf file
            log (_FILE, optional): file object to write stdout and stderr to. Defaults to None (i.e. output to stdout/stderr).
        """
        if path.with_suffix('.mmd').exists() and cache:
            return path.with_suffix('.mmd').read_text()

        assert path.exists(), f"file {path} does not exist"
        assert path.suffix == '.pdf', f"file {path} is not a pdf"
        result = subprocess.run(['nougat', str(path), '-o', str(path.parent), '-b',
                                str(self.batch_size)], stdout=log, stderr=log)
        assert result.returncode == 0, f"error extracting text from {path}"
        text = path.with_suffix('.mmd').read_text()
        if not cache:
            path.with_suffix('.mmd').unlink()
        return text

    def convert_to_paragraphs(self, text: str) -> list[str]:
        """break a string into paragraphs, filtering out ones that should not be used for semantic search"""
        def paragraph_filter(p): return not NougatExtractor.is_too_short(
            p, self.min_words) and not NougatExtractor.is_citation(p)
        paragraphs = list(filter(paragraph_filter, text.split('\n\n')))
        return paragraphs

    @staticmethod
    def is_too_short(paragraph: str, min_words: int) -> bool:
        """paragraph filter for checking if a paragraph is too short (by word count)"""
        return len(paragraph.split()) < min_words

    @staticmethod
    def is_citation(paragraph: str) -> bool:
        """paragraph filter for checking if a paragraph is a citation section"""
        patterns = [
            r"\*.*\(\d{4}\).*:.*\.",
            r"\*\s\[[^\]]+\d{4}\].*\.",
            r"\*\s\[[^\]]*\][^(\d{4})]*\d{4}.*",
            r"\*\s.*\d{4}.*\.\s(?:http|www)\S+",
            r"\*.*\d{4}\.\s[_\*]?[A-Za-z0-9][^\*]*?[_\*]?\.\s.*?\.",
        ]
        pattern = f'({")|(".join(patterns)})'
        lines = paragraph.split('\n')

        # count the number of lines that match the pattern
        num_matches = sum([1 for line in lines if re.match(pattern, line)])

        # if more than half the lines match the pattern, then it's a citation section
        # TODO: this should actually measure percentage of matched text to the total text
        return num_matches > len(lines)/2
