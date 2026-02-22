# encoding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import json

def _split_list(s: str):
    """
    支持两种写法：
    1) JSON 数组：["kw1", "kw2"]
    2) 逗号/分号分隔：kw1,kw2  或  kw1;kw2
    """
    if not s:
        return []
    s = s.strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            v = json.loads(s)
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
        except Exception:
            pass
    # fallback: split by , or ;
    parts = []
    for chunk in s.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


# ========== GitHub（建议用 Actions 的 GITHUB_TOKEN 或你自己的 GH_TOKEN secret） ==========
# 兼容原字段名：USERNAME/TOKEN/REPO_OWNER/REPO_NAME
USERNAME = os.getenv("GITHUB_USERNAME", "").strip()

# 优先 GH_TOKEN，再用 Actions 内置 GITHUB_TOKEN
TOKEN = (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()

# repo 信息（Actions 里建议在 workflow 里注入 REPO_OWNER/REPO_NAME）
REPO_OWNER = (os.getenv("REPO_OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or "").strip()
REPO_NAME = (os.getenv("REPO_NAME") or "").strip()
if not REPO_NAME:
    gh_repo = (os.getenv("GITHUB_REPOSITORY") or "").strip()  # owner/repo
    if "/" in gh_repo:
        REPO_NAME = gh_repo.split("/", 1)[1].strip()


# ========== arXiv ==========
NEW_SUB_URL = os.getenv("NEW_SUB_URL", "https://arxiv.org/list/cs/new").strip()

# 关键词（main.py 里用 KEYWORD_LIST 作为默认 filter_keys）
KEYWORD_LIST = _split_list(os.getenv("KEYWORD_LIST", "")) or ["remote sensing"]


# ========== OpenAI ==========
# 兼容原字段名：OPENAI_API_KEYS / LANGUAGE
# 推荐：只设一个 OPENAI_API_KEY；也可以设 OPENAI_API_KEYS（逗号分隔或 JSON 数组）
_openai_keys = _split_list(os.getenv("OPENAI_API_KEYS", ""))
_single_key = os.getenv("OPENAI_API_KEY", "").strip()
if _single_key:
    _openai_keys = [_single_key] + [k for k in _openai_keys if k != _single_key]

OPENAI_API_KEYS = _openai_keys or [""]  # 为空会导致摘要失败，但不会阻断整个流程
LANGUAGE = os.getenv("LANGUAGE", "zh").strip()  # zh | en
