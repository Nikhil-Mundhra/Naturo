# Core indexing, parsing, and search engine logic for Naturo Product Search

from .config import load_config, save_config, pick_root_dir, CONFIG_FILE
from .constants import TREE_CACHE_FILE, FILE_EXTS, MATERIAL_MAP, COLOR_MAP, DESIGN_CATEGORIES
from .folder_index import FolderIndex
from .matching import compute_match_score
from .parsing import normalize_token, make_searchable, build_selection

__all__ = [
    'load_config',
    'save_config',
    'pick_root_dir',
    'CONFIG_FILE',
    'TREE_CACHE_FILE',
    'FILE_EXTS',
    'MATERIAL_MAP',
    'COLOR_MAP',
    'DESIGN_CATEGORIES',
    'FolderIndex',
    'compute_match_score',
    'normalize_token',
    'make_searchable',
    'build_selection',
]
