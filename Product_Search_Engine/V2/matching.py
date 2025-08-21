import os
import re
from .parsing import normalize_token, make_searchable, generate_size_variants

def score_supplier_selected_path(path, supplier_code):
    base = normalize_token(os.path.basename(path))
    sc = normalize_token(supplier_code or "")
    score = 0
    if sc and re.search(rf'(^|_){re.escape(sc)}(_|$)', base):
        score += 3
    if "selected" in base:
        score += 4
    if "item" in base:
        score += 1
    score += max(0, 3 - len(path.split(os.sep)) % 3)
    return score

def color_matches(searchable, required_colors):
    for col in required_colors:
        coln = normalize_token(col)
        if re.search(r'(^|_)' + re.escape(coln) + r'(_|$)', searchable):
            return True
        if coln in searchable:
            return True
    return False

def matches_size(searchable, required_sizes):
    if not required_sizes:
        return True
    for sz in required_sizes:
        variants = generate_size_variants(sz)
        for v in variants:
            if v and v in searchable:
                return True
    return False

def file_token_match(searchable, file_token):
    if not file_token:
        return True
    ft_norm = make_searchable(file_token)
    if not ft_norm:
        return True
    return ft_norm in searchable

def design_matches(searchable: str, design_codes: list[str]) -> bool:
    if not design_codes:
        return True
    for dc in design_codes:
        dcn = normalize_token(dc)
        if not dcn:
            continue
        if re.search(r'(^|_)' + re.escape(dcn) + r'(_|$)', searchable):
            return True
        if dcn in searchable:
            return True
    return False

def compute_match_score(searchable: str,
                        material_codes: list[str],
                        color_codes: list[str],
                        size_tokens: list[str],
                        design_codes: list[str],
                        file_token: str | None) -> tuple[int, list[str]]:
    """
    Return (score, missing_list). Higher score means better match.
    Scoring:
      +3 material present (if any selected)
      +3 color present (if any selected)
      +3 size present (if any selected; any variant match qualifies)
      +2 design present (if any selected)
      +3 file_token present (if provided)
    Missing parts recorded in 'missing_list'.
    """
    score = 0
    missing = []

    # material
    if material_codes:
        if any(normalize_token(m) in searchable for m in material_codes):
            score += 3
        else:
            missing.append("material")

    # color
    if color_codes:
        if color_matches(searchable, [normalize_token(c) for c in color_codes]):
            score += 3
        else:
            missing.append("color")

    # size
    if size_tokens:
        ok = False
        for sz in size_tokens:
            variants = generate_size_variants(sz)
            for v in variants:
                if v and v in searchable:
                    ok = True
                    break
            if ok:
                break
        if ok:
            score += 3
        else:
            missing.append("size")

    # designs
    if design_codes:
        if design_matches(searchable, design_codes):
            score += 2
        else:
            missing.append("design")

    # file token
    if file_token:
        if file_token_match(searchable, file_token):
            score += 3
        else:
            missing.append("file_token")

    return score, missing
