"""Video Processing Module - Composes educational UPSC videos"""

from .composer import VideoComposer, EducationalContent, CompositionResult
from .thumbnail import ThumbnailGenerator
from .effects import VideoEffects
from .educational_effects import (
    EducationalEffects,
    KeyPointDisplay,
    FactCard,
    TopicHeader,
    ImageOverlay
)

__all__ = [
    "VideoComposer",
    "EducationalContent",
    "CompositionResult",
    "ThumbnailGenerator",
    "VideoEffects",
    "EducationalEffects",
    "KeyPointDisplay",
    "FactCard",
    "TopicHeader",
    "ImageOverlay"
]
