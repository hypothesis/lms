import re

from bin.jstor_mapping_demo.matcher import Match

SCORE_THRESHOLDS = ((20, "excellent"), (15, "good"), (8, "ok"), (0, "dubious"))


def evaluate_match(match: Match):
    perfect_id = False
    if match.jstor_record.id in match.application_instance.domains:
        perfect_id = True

    perfect_name = False
    norm_jstor = _normalize_string(match.jstor_record.name)
    for name in match.application_instance.names:
        if _normalize_string(name) == norm_jstor:
            perfect_name = True

    if perfect_name and perfect_id:
        return "perfect name+id"
    if perfect_name:
        return "perfect name"
    if perfect_id:
        return "perfect id"

    for threshold, description in SCORE_THRESHOLDS:
        if match.score >= threshold:
            return description

    assert False, "Not possible?"


STOP_WORDS = {"of", "the", "and", "&", "at", "moodle", "blackboard"}
NORMALIZE_WORDS = {"saint": "st", "university": "uni"}


def _normalize_string(string):
    cleaned = string.lower()
    cleaned = re.sub("[-_,.@+():'ʻ/]+", "", cleaned)
    cleaned = re.sub(" +", " ", cleaned)
    cleaned = cleaned.replace("&", "and")

    parts = []
    for part in cleaned.strip().split(" "):
        if part in STOP_WORDS:
            continue
        parts.append(NORMALIZE_WORDS.get(part, part))

    return " ".join(parts)
