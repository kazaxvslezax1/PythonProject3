"""Shared, candle-local quality and volume gate for PAPER entry eligibility."""

import math
from dataclasses import dataclass

MIN_ENTRY_QUALITY = 7.0
MIN_ENTRY_VOLUME_RATIO = 1.5
PREFILTER_REJECTED = "PREFILTER_REJECTED"
AI_REQUEST_POLICY = "post-prefilter-v1"
LEGACY_AI_REQUEST_POLICY = "pre-prefilter-v1"


@dataclass(frozen=True)
class EntryPrefilterResult:
    passed: bool
    reason: str
    quality: float
    volume_ratio: float
    min_quality: float
    min_volume_ratio: float


def evaluate_entry_prefilter(
    quality,
    volume_ratio,
    *,
    min_quality=MIN_ENTRY_QUALITY,
    min_volume_ratio=MIN_ENTRY_VOLUME_RATIO,
):
    """Apply the existing manager's first two checks, without portfolio state."""
    if not all(math.isfinite(x) for x in (quality, volume_ratio)):
        reason = "Invalid quality or volume"
    elif quality < min_quality or volume_ratio < min_volume_ratio:
        reason = "Quality or volume filter rejected"
    else:
        reason = "Paper entry prefilter passed"
    return EntryPrefilterResult(
        passed=reason == "Paper entry prefilter passed",
        reason=reason,
        quality=quality,
        volume_ratio=volume_ratio,
        min_quality=min_quality,
        min_volume_ratio=min_volume_ratio,
    )
