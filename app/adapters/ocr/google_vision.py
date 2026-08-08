import logging

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import vision

from app.adapters.ocr.base import OCRProviderError
from app.services.domain import BoundingBox, TextLine

logger = logging.getLogger(__name__)

# A horizontal gap between adjacent words wider than this many "average
# character widths" is treated as a column separator in a tabular layout
# (test name -> value -> unit -> range) rather than a normal inter-word
# space, and gets emitted as 2+ spaces so lines.py's field splitter picks
# it up as a column boundary rather than a run-on phrase.
_GAP_MULTIPLIER = 2.0

# Two words are considered to be on the same line if their vertical
# midpoints differ by no more than this fraction of a word's height --
# deliberately rough, not a true geometric alignment model.
_VERTICAL_TOLERANCE_RATIO = 0.5


class _Word:
    __slots__ = ("text", "min_x", "max_x", "min_y", "max_y")

    def __init__(self, text: str, min_x: float, max_x: float, min_y: float, max_y: float) -> None:
        self.text = text
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    @property
    def mid_y(self) -> float:
        return (self.min_y + self.max_y) / 2

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def char_width(self) -> float:
        length = len(self.text)
        return (self.max_x - self.min_x) / length if length > 0 else 0.0


def _extract_words(response: "vision.AnnotateImageResponse") -> list[_Word]:
    words: list[_Word] = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    text = "".join(symbol.text for symbol in word.symbols)
                    if not text:
                        continue
                    xs = [v.x for v in word.bounding_box.vertices]
                    ys = [v.y for v in word.bounding_box.vertices]
                    words.append(_Word(text, min(xs), max(xs), min(ys), max(ys)))
    return words


def _cluster_into_lines(words: list[_Word]) -> list[list[_Word]]:
    """Groups words into lines by vertical alignment, then sorts each line
    left-to-right. Words are processed in top-to-bottom order, so the
    resulting cluster list is already top-to-bottom -- no separate sort of
    lines is needed."""
    if not words:
        return []

    ordered = sorted(words, key=lambda w: w.mid_y)
    clusters: list[list[_Word]] = [[ordered[0]]]
    for word in ordered[1:]:
        cluster = clusters[-1]
        cluster_mid_y = sum(w.mid_y for w in cluster) / len(cluster)
        tolerance = max(w.height for w in cluster) * _VERTICAL_TOLERANCE_RATIO
        if abs(word.mid_y - cluster_mid_y) <= tolerance:
            cluster.append(word)
        else:
            clusters.append([word])

    for cluster in clusters:
        cluster.sort(key=lambda w: w.min_x)
    return clusters


def _join_words(words: list[_Word]) -> str:
    parts = [words[0].text]
    for prev, curr in zip(words, words[1:]):
        gap = curr.min_x - prev.max_x
        avg_char_width = (prev.char_width + curr.char_width) / 2
        separator = "  " if avg_char_width > 0 and gap > avg_char_width * _GAP_MULTIPLIER else " "
        parts.append(separator)
        parts.append(curr.text)
    return "".join(parts)


def _line_bounding_box(words: list[_Word]) -> BoundingBox:
    min_x = min(w.min_x for w in words)
    max_x = max(w.max_x for w in words)
    min_y = min(w.min_y for w in words)
    max_y = max(w.max_y for w in words)
    return BoundingBox(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


class GoogleVisionAdapter:
    """Calls Cloud Vision's DOCUMENT_TEXT_DETECTION and reconstructs lines
    from its page/block/paragraph/word hierarchy, since Vision has no
    concept of a "line" itself."""

    def __init__(self, credentials_path: str | None = None) -> None:
        if credentials_path:
            self._client = vision.ImageAnnotatorClient.from_service_account_file(credentials_path)
        else:
            self._client = vision.ImageAnnotatorClient()

    @property
    def name(self) -> str:
        return "google_vision"

    def extract_text(self, image_bytes: bytes) -> list[TextLine]:
        image = vision.Image(content=image_bytes)

        try:
            response = self._client.document_text_detection(image=image)
        except GoogleAPICallError as exc:
            message = f"Vision API request failed: {exc}"
            logger.error(message)
            raise OCRProviderError(message) from exc

        if response.error.message:
            message = f"Vision API returned an error: {response.error.message}"
            logger.error(message)
            raise OCRProviderError(message)

        clusters = _cluster_into_lines(_extract_words(response))
        return [
            TextLine(text=_join_words(cluster), bounding_box=_line_bounding_box(cluster))
            for cluster in clusters
        ]
