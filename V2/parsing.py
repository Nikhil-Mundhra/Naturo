import re
from .constants import MATERIAL_MAP, COLOR_MAP, DESIGN_CATEGORIES, DESIGN_CODES_LOWER, SUPPLIER_CODES_LOWER

def normalize_token(s):
    import re
    return re.sub(r'[^0-9a-z]+', '_', (s or "").lower()).strip('_')

def make_searchable(name):
    return normalize_token(name)

def normalize_size_token(s):
    if not s:
        return s
    x = s.replace('"', '_').replace('.', '_').replace(' ', '_')
    x = x.replace('’', '_').replace('‘', '_').replace('“', '_').replace('”', '_').replace("'", "_")
    x = re.sub(r'__+', '_', x)
    return x.lower()

def generate_size_variants(sz):
    if not sz:
        return set()
    base = normalize_size_token(sz)
    variants = set([base, base.replace('_', '')])
    base_no_suffix = re.sub(r'(?:_)?[fl]$', '', base)
    variants.update([base_no_suffix, base_no_suffix.replace('_', ''), base.replace('_', '"'), re.sub(r'[^0-9]', '', base)])
    return {v for v in variants if v}

def normalize_input(code):
    s = re.sub(r'[^0-9A-Za-z_"]+', '_', (code or ""))
    s = re.sub(r'__+', '_', s)
    return [t for t in s.split('_') if t]

def is_mrp_token(t: str) -> bool:
    tl = (t or "").lower()
    if tl == "mrp":
        return True
    if re.fullmatch(r'mrp\d+', tl):
        return True
    return False

def is_design_token(t: str) -> bool:
    tl = (t or "").lower()
    if tl in DESIGN_CODES_LOWER:
        return True
    if re.fullmatch(r'\d+l', tl):
        return True
    return False

def is_height_feet_token(t: str) -> bool:
    return bool(re.fullmatch(r'\d+(?:\.\d+)?f', (t or '').lower()))

def inches_fragment(s: str) -> str | None:
    m = re.match(r'^(\d+)"', (s or ''))
    return m.group(1) + '"' if m else None

def leftover_after_inches(s: str) -> str:
    m = re.match(r'^\d+"(.*)$', (s or ''))
    return m.group(1) if m else ''

def normalize_height_token(h: str) -> str:
    return normalize_size_token(h)

def normalize_inches_token(w: str) -> str:
    return normalize_size_token(w)

def normalize_alnum_only(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def extract_series_signatures(code: str):
    sig = normalize_alnum_only(code)
    rev = sig[::-1]
    out = set()
    if sig:
        out.add(sig)
    if rev and rev != sig:
        out.add(rev)
    return out

def path_contains_any_signature(rel_path: str, signatures: set) -> bool:
    p = normalize_alnum_only(rel_path)
    return any(sig in p for sig in signatures if sig)

def parse_product_code(code: str):
    tokens = normalize_input(code)

    material_codes = [v.lower() for v in MATERIAL_MAP.values()]
    color_codes = [v.lower() for v in COLOR_MAP.values()]

    prefix = []
    material = []
    color = []
    supplier = None
    folder_code = None
    file_token = None
    size = []

    found_material = False
    i = 0
    while i < len(tokens):
        t = tokens[i]
        tl = t.lower()

        if is_mrp_token(tl):
            if tl == "mrp" and i + 1 < len(tokens) and re.fullmatch(r'\d+', tokens[i + 1].lower()):
                i += 2
                continue
            i += 1
            continue

        if not found_material and tl in material_codes:
            found_material = True
            material.append(tl)
            i += 1
            continue
        if not found_material:
            prefix.append(t)
            i += 1
            continue

        if tl in material_codes:
            material.append(tl)
            i += 1
            continue
        if tl in color_codes:
            color.append(tl)
            i += 1
            continue

        if is_height_feet_token(tl):
            size.append(normalize_height_token(t))
            i += 1
            continue
        if re.fullmatch(r'\d+"', t):
            size.append(normalize_inches_token(t))
            i += 1
            continue

        inc = inches_fragment(t)
        if inc:
            size.append(normalize_inches_token(inc))
            rest = leftover_after_inches(t)
            next_t = tokens[i + 1].lower() if i + 1 < len(tokens) else ''
            if rest and is_height_feet_token(next_t):
                height = f"{rest}.{next_t[:-1]}F" if re.fullmatch(r'\d+', rest) else next_t.upper()
                size.append(normalize_height_token(height))
                i += 2
                continue
            if rest and rest.lower().endswith('f') and is_height_feet_token(rest.lower()):
                size.append(normalize_height_token(rest))
                i += 1
                continue
            i += 1
            continue

        if is_design_token(t):
            i += 1
            continue

        if not folder_code:
            folder_code = tl
        elif not supplier:
            if tl in SUPPLIER_CODES_LOWER:
                supplier = tl
            else:
                if not file_token:
                    file_token = tl
        else:
            if not file_token:
                file_token = tl

        i += 1

    return {
        "prefix": "_".join(prefix) if prefix else None,
        "material": material,
        "color": color,
        "size": size,
        "supplier": supplier,
        "folder_code": folder_code,
        "file_token": file_token,
        "tokens": tokens
    }

def build_selection(material: str | None,
                    height: str | None,
                    width_inches: str | None,
                    color: str | None,
                    designs: list[str] | None,
                    supplier: str | None = None,
                    folder_code: str | None = None,
                    file_token: str | None = None) -> dict:
    """
    Build a normalized selection dict that mirrors the structure used by parse_product_code output,
    but based on UI questionnaire inputs. All fields are normalized to downstream expectations.
    - material: label from MATERIAL_MAP keys (e.g. "PVC") or already code ("PV"). We store codes (lowercase).
    - height: values like '8F', '9F', '9.5F' or '' -> normalized via normalize_height_token
    - width_inches: raw inches like '12' or '12"' -> normalized to '12"' variant as parse_product_code would
    - color: label from COLOR_MAP keys (e.g. "Black") or already code ("BL"). We store codes (lowercase).
    - designs: list of design labels (must map to DESIGN_CATEGORIES codes). Stored as design codes (lowercase).
    - supplier: optional supplier code (lowercase)
    - folder_code: optional folder code token (lowercase)
    - file_token: optional additional file token filter (lowercase)
    """
    # Map material/color labels to codes if they are labels
    mat_codes = {k.lower(): v.lower() for k, v in MATERIAL_MAP.items()}
    col_codes = {k.lower(): v.lower() for k, v in COLOR_MAP.items()}
    # Flatten design maps
    design_codes = {}
    for cat, mapping in DESIGN_CATEGORIES.items():
        for label, code in mapping.items():
            design_codes[label.lower()] = code.lower()

    material_list = []
    if material:
        ml = material.lower()
        if ml in mat_codes:
            material_list.append(mat_codes[ml])
        else:
            material_list.append(ml)

    color_list = []
    if color:
        cl = color.lower()
        if cl in col_codes:
            color_list.append(col_codes[cl])
        else:
            color_list.append(cl)

    size_list = []
    # normalize height
    if height:
        size_list.append(normalize_height_token(height))
    # normalize width inches
    if width_inches:
        w = width_inches.strip()
        if not w.endswith('"'):
            # accept 12 or 12" or 12in formats
            w = re.sub(r'[^0-9]+', '', w) + '"'
        size_list.append(normalize_inches_token(w))

    # designs to codes (lowercase)
    design_list = []
    for d in designs or []:
        dl = (d or "").strip().lower()
        if not dl:
            continue
        if dl in design_codes:
            design_list.append(design_codes[dl])
        else:
            # if user typed code directly
            design_list.append(dl)

    sel = {
        "material": material_list,       # list of codes (lowercase)
        "color": color_list,             # list of codes (lowercase)
        "size": size_list,               # list of normalized size tokens (as parse does)
        "designs": design_list,          # optional design codes to require
        "supplier": normalize_token(supplier) if supplier else None,
        "folder_code": normalize_token(folder_code) if folder_code else None,
        "file_token": normalize_token(file_token) if file_token else None,
    }
    return sel
