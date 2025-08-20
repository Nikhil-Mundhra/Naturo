import os
import re
import json
import hashlib
from time import time
from typing import Optional, Iterable, List, Dict, Tuple, Any
from .constants import TREE_CACHE_FILE, FILE_EXTS
from .parsing import (
    normalize_token, make_searchable,
    extract_series_signatures, path_contains_any_signature,
    parse_product_code
)
from .matching import (
    score_supplier_selected_path, color_matches,
    matches_size, file_token_match
)

from dataclasses import dataclass
from functools import total_ordering

@total_ordering
@dataclass(frozen=True)
class SupplierCandidate:
    score: int
    node: Any

    def __lt__(self, other: "SupplierCandidate") -> bool:
        if not isinstance(other, SupplierCandidate):
            return NotImplemented
        if self.score != other.score:
            return self.score < other.score
        self_key = getattr(self.node, "name", None) or getattr(self.node, "path", None) or id(self.node)
        other_key = getattr(other.node, "name", None) or getattr(other.node, "path", None) or id(other.node)
        return self_key < other_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SupplierCandidate):
            return NotImplemented
        return self.score == other.score and self.node is other.node


class FolderIndex:
    """
    In-memory folder tree persisted to TREE_CACHE_FILE.
    Node format:
      {"_path": "...", "_files": [...], "Subfolder Name": { ... } }
    """
    def __init__(self, root_dir, cache_file=TREE_CACHE_FILE, force_rebuild=False):
        self.root_dir = root_dir
        self.cache_file = cache_file
        self.tree = None
        self.hash = None
        self.last_built = None
        self.load_or_build(force_rebuild)

    def compute_dir_hash(self):
        hasher = hashlib.md5()
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            hasher.update(dirpath.encode('utf-8', 'ignore'))
            try:
                m = os.path.getmtime(dirpath)
                hasher.update(str(m).encode('utf-8', 'ignore'))
            except Exception:
                pass
            for fn in sorted(filenames):
                try:
                    full = os.path.join(dirpath, fn)
                    m = os.path.getmtime(full)
                    hasher.update(fn.encode('utf-8', 'ignore'))
                    hasher.update(str(m).encode('utf-8', 'ignore'))
                except Exception:
                    continue
        return hasher.hexdigest()

    def build_tree(self):
        start = time()
        def _build(path):
            node = {"_path": path, "_files": []}
            try:
                entries = list(os.scandir(path))
            except Exception:
                entries = []
            for entry in sorted(entries, key=lambda e: e.name):
                try:
                    if not entry.is_file():
                        continue
                    name_raw = entry.name
                    name_norm = name_raw.strip().lower().rstrip('.')
                    has_ext = any(name_norm.endswith(ext) for ext in (e.lower() for e in FILE_EXTS))
                    is_extensionless = ('.' not in os.path.basename(name_raw))
                    if has_ext or is_extensionless:
                        node["_files"].append(entry.name)
                except Exception:
                    continue
            for entry in sorted(entries, key=lambda e: e.name):
                try:
                    if entry.is_dir():
                        if entry.name in ('.git',):
                            continue
                        node[entry.name] = _build(os.path.join(path, entry.name))
                except Exception:
                    continue
            return node

        self.tree = _build(self.root_dir)
        self.last_built = time() - start
        return self.tree

    def load_cache(self):
        if not os.path.exists(self.cache_file):
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_cache(self, dir_hash):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({"hash": dir_hash, "root": self.tree}, f)
        except Exception as e:
            print("Failed to save tree cache:", e)

    def load_or_build(self, force=False):
        if not os.path.isdir(self.root_dir):
            self.tree = None
            return
        current_hash = self.compute_dir_hash()
        cached = None if force else self.load_cache()
        if cached and cached.get("hash") == current_hash and "root" in cached:
            self.tree = cached["root"]
            self.hash = current_hash
            return
        self.build_tree()
        self.hash = current_hash
        self.save_cache(current_hash)

    def rebuild(self):
        self.load_or_build(force=True)

    def _iterate_all_nodes_with_names(self) -> Iterable[Tuple[str, Dict]]:
        if not self.tree:
            return
        import os as _os
        root_name = _os.path.basename(self.root_dir) or ""
        stack = [(root_name, self.tree)]
        while stack:
            name, node = stack.pop()
            yield name, node
            for k, v in node.items():
                if k in ("_path", "_files"):
                    continue
                stack.append((k, v))

    def iter_supplier_nodes(self, supplier: str) -> Iterable[Dict]:
        """Yield all nodes that might contain supplier folders"""
        for name, node in self._iterate_all_nodes_with_names():
            yield node

    def score_supplier_node(self, node: Dict, supplier: str) -> int:
        """Score a node for supplier relevance"""
        path = node.get("_path", "")
        return score_supplier_selected_path(path, supplier)

    def pick_best_by_score(self, nodes: Iterable, score_fn) -> Optional[Dict]:
        best: Optional[SupplierCandidate] = None
        for n in nodes:
            sc = score_fn(n)
            if not isinstance(sc, int):
                raise TypeError(f"score_fn must return int, got {type(sc)} for {n!r}")
            cand = SupplierCandidate(sc, n)
            if best is None or best < cand:
                best = cand
        return None if best is None else best.node

    def find_supplier_selected_folder(self, supplier: str) -> Optional[Dict]:
        return self.pick_best_by_score(
            self.iter_supplier_nodes(supplier),
            lambda node: self.score_supplier_node(node, supplier),
            )

    def find_folder_with_code(self, parent_node: Dict, folder_code: str, supplier_prefix: Optional[str] = None) -> Tuple[Optional[Dict], int, int]:
        if not parent_node or not folder_code:
            return None, -1, 10**9
        fc = normalize_token(folder_code)
        sp = normalize_token(supplier_prefix) if supplier_prefix else None
        best = (None, -1, 10**9)
        parent_depth = len(parent_node.get("_path", "").split(os.sep))
        stack = [parent_node]
        while stack:
            node = stack.pop()
            base = normalize_token(os.path.basename(node.get("_path", "")))
            score = 0
            if re.search(rf'(^|_){re.escape(fc)}(_|$)', base):
                score += 5
            if sp and sp in base:
                score += 2
            if score > 0:
                depth = len(node.get("_path", "").split(os.sep)) - parent_depth
                if score > best[1] or (score == best[1] and depth < best[2]):
                    best = (node, score, depth)
            for k, v in node.items():
                if k in ("_path", "_files"):
                    continue
                stack.append(v)
        return best

    def choose_subdir_matching_code(self, node: Dict, folder_code: str) -> List[Dict]:
        if not folder_code or not node:
            return []
        fc = normalize_token(folder_code)
        matched = []
        for name, child in node.items():
            if name in ("_path", "_files"):
                continue
            nb = normalize_token(name)
            if re.search(rf'(^|_){re.escape(fc)}(_|$)', nb):
                matched.append(child)
        return matched

    def descend_to_images_or_branch(self, start_node: Dict, folder_code: Optional[str] = None, allow_images: bool = False) -> Tuple[Optional[Dict], str]:
        if not start_node:
            return None, "invalid_start"
        current = start_node
        visited = set()
        reason = ""
        while True:
            path = current.get("_path", "")
            if path in visited:
                reason = "invalid_or_cycle"
                break
            visited.add(path)
            if allow_images:
                cached = current.get("_files", [])
                if cached:
                    reason = "images_found_here"
                    break
                # Fallback to disk scan if cache is empty
                try:
                    if any(entry.is_file() for entry in os.scandir(path)):
                        reason = "images_found_here"
                        break
                except Exception:
                    pass
            children = [(name, child) for name, child in current.items() 
                        if name not in ("_path", "_files")]
            if not children:
                reason = "no_subdirs"
                break
            if len(children) > 1:
                matches = self.choose_subdir_matching_code(current, folder_code)
                if len(matches) == 1:
                    current = matches[0]
                    continue
                elif len(matches) > 1:
                    reason = "multiple_matches_stop"
                    break
                else:
                    reason = "multiple_subdirs_none_match_code"
                    break
            # Exactly one child - get the node from the tuple
            _, current = children[0]
        return current, reason

    def collect_candidate_files(self, start_node: Dict) -> List[str]:
            if not start_node:
                return []
            out = []
            stack = [start_node]

            exts_lower = tuple(ext.lower() for ext in FILE_EXTS)

            def normalize_name(name: str) -> str:
                n = ''.join(ch for ch in name if ch not in ('\u200b', '\u200c', '\u200d'))
                n = n.replace('\u00a0', ' ')
                n = n.strip().lower().rstrip('.')
                return n

            def has_valid_ext(name: str) -> bool:
                nn = normalize_name(name)
                return nn.endswith(exts_lower)

            while stack:
                node = stack.pop()
                base_path = node.get("_path", "")

                # Use cached files from tree instead of disk scan
                cached = node.get("_files", []) or []
                for fn in cached:
                    try:
                        full = os.path.join(base_path, fn)
                        if os.path.isfile(full):
                            basename = os.path.basename(fn)
                            if has_valid_ext(basename) or ('.' not in basename):
                                out.append(full)
                    except Exception:
                        continue

                # Add child directories to stack
                for k, child in node.items():
                    if k in ("_path", "_files"):
                        continue
                    stack.append(child)

            return out

    def search_by_selection(self, selection: dict, max_suggestions: int = 200) -> tuple[dict, list[str], list[tuple[str, list[str], int]]]:
        """
        Perform questionnaire search based on normalized selection dict from build_selection().
        Returns:
        debug_info: dict (similar structure to debug_search_files)
        exact_matches: list[str] (absolute paths)
        suggestions: list of tuples (path, missing_parts, score) sorted by score desc
        """
        supplier = selection.get("supplier")
        folder_code = selection.get("folder_code")
        materials = [normalize_token(m) for m in (selection.get("material") or [])]
        colors = [normalize_token(c) for c in (selection.get("color") or [])]
        sizes = selection.get("size") or []
        designs = selection.get("designs") or []
        file_token = selection.get("file_token")

        # pick search root
        search_node = self.tree
        sup_node = None
        if supplier:
            sup_node = self.find_supplier_selected_folder(supplier)
            if sup_node:
                search_node = sup_node

        fc_node = None
        if folder_code and search_node:
            fc_node, _, _ = self.find_folder_with_code(search_node, folder_code, supplier_prefix=supplier)
            if fc_node:
                search_node = fc_node

        final_node, stop_reason = self.descend_to_images_or_branch(search_node, folder_code, allow_images=True)
        node_for_scan = final_node or search_node

        # scan candidates once
        candidate_files = self.collect_candidate_files(node_for_scan)
        base_root = node_for_scan.get("_path") if node_for_scan else self.root_dir

        # strict filter = all provided criteria must match
        exact_matches = []
        suggestions = []

        for p in candidate_files:
            rel = os.path.relpath(p, base_root) if base_root else os.path.basename(p)
            s = make_searchable(rel)

            # Compute score and missing parts
            sc, missing = compute_match_score(
                s,
                materials,
                colors,
                sizes,
                designs,
                file_token,
            )

            # Strict logic: if a criterion was provided, it must not be missing.
            criteria_provided = {
                "material": bool(materials),
                "color": bool(colors),
                "size": bool(sizes),
                "design": bool(designs),
                "file_token": bool(file_token),
            }
            any_missing_provided = any(criteria_provided.get(m, False) for m in missing)

            if not any_missing_provided:
                exact_matches.append(p)
            else:
                # Only add as suggestion if it matches something (score>0)
                if sc > 0:
                    suggestions.append((p, missing, sc))

        # rank suggestions by score desc, then by filename asc
        suggestions.sort(key=lambda x: (-x[2], os.path.basename(x).lower()))
        if max_suggestions is not None:
            suggestions = suggestions[:max_suggestions]

        debug = {
            "selection": selection,
            "initial_root": self.root_dir,
            "supplier_folder_found": sup_node.get("_path") if sup_node else None,
            "folder_code_folder_found": fc_node.get("_path") if fc_node else None,
            "autodescent_final_root": (final_node or search_node).get("_path") if (final_node or search_node) else None,
            "autodescent_stop_reason": stop_reason,
            "candidate_count": len(candidate_files),
            "matches_count": len(exact_matches),
            "suggestions_count": len(suggestions),
            "sample_suggestions": [(p, missing, sc) for (p, missing, sc) in suggestions[:60]],
        }
        return debug, exact_matches, suggestions


    def search_files(self, code: str) -> List[str]:
        parsed = parse_product_code(code)
        supplier = parsed["supplier"]
        folder_code = parsed["folder_code"]
        materials = [normalize_token(m) for m in parsed["material"]]
        colors = [normalize_token(c) for c in parsed["color"]]
        sizes = parsed["size"]
        file_token = parsed["file_token"]

        search_node = self.tree
        sup_node = None
        if supplier:
            sup_node = self.find_supplier_selected_folder(supplier)
            if sup_node:
                search_node = sup_node

        fc_node = None
        if folder_code and search_node:
            fc_node, _, _ = self.find_folder_with_code(search_node, folder_code, supplier_prefix=supplier)
            if fc_node:
                search_node = fc_node

        final_node, _ = self.descend_to_images_or_branch(search_node, folder_code, allow_images=True)
        node_for_scan = final_node or search_node
        candidate_files = self.collect_candidate_files(node_for_scan)
        base_root = node_for_scan.get("_path") if node_for_scan else self.root_dir

        series_signatures = extract_series_signatures(code)

        results = []
        for p in candidate_files:
            rel = os.path.relpath(p, base_root) if base_root else os.path.basename(p)
            s = make_searchable(rel)

            if path_contains_any_signature(rel, series_signatures):
                results.append(p)
                continue

            if materials and not any(m in s for m in materials):
                continue
            if colors and not color_matches(s, colors):
                continue
            if sizes and not matches_size(s, sizes):
                continue
            if not file_token_match(s, file_token):
                continue
            results.append(p)
        return results

    def debug_search_files(self, code: str, max_show: int = 60) -> Tuple[Dict, List[str]]:
        parsed = parse_product_code(code)
        supplier = parsed["supplier"]
        folder_code = parsed["folder_code"]
        materials = [normalize_token(m) for m in parsed["material"]]
        colors = [normalize_token(c) for c in parsed["color"]]
        sizes = parsed["size"]
        file_token = parsed["file_token"]

        search_node = self.tree
        sup_node = None
        if supplier:
            sup_node = self.find_supplier_selected_folder(supplier)
            if sup_node:
                search_node = sup_node

        fc_node = None
        if folder_code and search_node:
            fc_node, _, _ = self.find_folder_with_code(search_node, folder_code, supplier_prefix=supplier)
            if fc_node:
                search_node = fc_node

        final_node, stop_reason = self.descend_to_images_or_branch(search_node, folder_code, allow_images=True)
        node_for_scan = final_node or search_node
        candidate_files = self.collect_candidate_files(node_for_scan)
        base_root = node_for_scan.get("_path") if node_for_scan else self.root_dir

        series_signatures = extract_series_signatures(code)

        matches, reasons = [], []
        for p in candidate_files:
            rel = os.path.relpath(p, base_root) if base_root else os.path.basename(p)
            s = make_searchable(rel)

            if path_contains_any_signature(rel, series_signatures):
                matches.append(p)
                continue

            fail = []
            if materials and not any(m in s for m in materials):
                fail.append("material")
            if colors and not color_matches(s, colors):
                fail.append("color")
            if sizes and not matches_size(s, sizes):
                fail.append("size")
            if not file_token_match(s, file_token):
                fail.append("file_token")
            if fail:
                reasons.append((p, fail))
            else:
                matches.append(p)

        debug = {
            "parsed": parsed,
            "initial_root": self.root_dir,
            "supplier_folder_found": sup_node.get("_path") if sup_node else None,
            "folder_code_folder_found": fc_node.get("_path") if fc_node else None,
            "autodescent_final_root": (final_node or search_node).get("_path") if (final_node or search_node) else None,
            "autodescent_stop_reason": stop_reason,
            "candidate_count": len(candidate_files),
            "matches_count": len(matches),
            "matches": matches[:max_show],
            "rejections": reasons[:max_show]
        }
        return debug, matches