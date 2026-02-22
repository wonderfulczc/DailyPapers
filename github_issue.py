# encoding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import requests
from urllib.parse import quote

# 兼容旧 config.py（如果你本地/仓库里还在用）
try:
    from config import USERNAME as _CFG_USERNAME  # 可空
    from config import TOKEN as _CFG_TOKEN        # 可空
    from config import REPO_OWNER as _CFG_OWNER   # 可空
    from config import REPO_NAME as _CFG_REPO     # 可空
except Exception:
    _CFG_USERNAME = ""
    _CFG_TOKEN = ""
    _CFG_OWNER = ""
    _CFG_REPO = ""

GITHUB_API = os.getenv("GITHUB_API", "https://api.github.com")


def _get_token():
    """
    推荐：在 GitHub Actions 里用 GITHUB_TOKEN（或你自建的 GH_TOKEN secret）。
    - GH_TOKEN: 你自己创建的 PAT / fine-grained token
    - GITHUB_TOKEN: Actions 内置 token
    - config.TOKEN: 兼容旧配置
    """
    return (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or _CFG_TOKEN or "").strip()


def _get_repo():
    """
    优先从环境变量拿（Actions 更安全），拿不到再回退到 config.py
    """
    owner = (os.getenv("REPO_OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or _CFG_OWNER or "").strip()

    repo = (os.getenv("REPO_NAME") or "").strip()
    if not repo:
        gh_repo = (os.getenv("GITHUB_REPOSITORY") or "").strip()  # e.g. "owner/repo"
        if "/" in gh_repo:
            repo = gh_repo.split("/", 1)[1].strip()
        else:
            repo = (_CFG_REPO or "").strip()

    if not owner or not repo:
        raise RuntimeError("Missing repo info. Please set REPO_OWNER/REPO_NAME (or GITHUB_REPOSITORY in Actions).")
    return owner, repo


def _headers(token: str):
    if not token:
        raise RuntimeError("Missing GitHub token. Please set GH_TOKEN or use GITHUB_TOKEN in Actions.")
    return {
        "Authorization": "Bearer %s" % token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _request(method: str, url: str, token: str, expected_status=(200,), **kwargs):
    r = requests.request(method, url, headers=_headers(token), timeout=30, **kwargs)
    if r.status_code not in expected_status:
        raise RuntimeError(
            "GitHub API error: %s %s -> %s\n%s"
            % (method, url, r.status_code, r.text)
        )
    return r


def _ensure_labels(owner: str, repo: str, labels, token: str):
    """
    可选：自动创建不存在的 label（避免因为 labels 不存在导致 422）。
    """
    if not labels:
        return

    for name in labels:
        if not name:
            continue
        name = str(name).strip()
        if not name:
            continue

        # GET label（label 名称要 URL encode）
        get_url = f"{GITHUB_API}/repos/{owner}/{repo}/labels/{quote(name, safe='')}"
        r = requests.get(get_url, headers=_headers(token), timeout=30)

        if r.status_code == 200:
            continue
        if r.status_code != 404:
            # 其它错误直接抛出，便于你在 Actions log 里定位
            raise RuntimeError("Get label failed: %s -> %s\n%s" % (get_url, r.status_code, r.text))

        # 不存在则创建
        create_url = f"{GITHUB_API}/repos/{owner}/{repo}/labels"
        payload = {"name": name, "color": "ededed"}  # color 必填
        # 201 created；422 可能是并发创建/重名，允许通过
        _request("POST", create_url, token, expected_status=(201, 422), json=payload)


def make_github_issue(title, body=None, assignee=None, closed=False, labels=None):
    """
    标准创建 Issue：
    POST /repos/{owner}/{repo}/issues

    兼容原项目的函数签名（main.py 里直接调用）。
    - assignee / closed 这里不强依赖：默认不传，避免无权限导致失败
    """
    token = _get_token()
    owner, repo = _get_repo()

    # labels 规范化
    if labels is None:
        labels = []
    if not isinstance(labels, (list, tuple)):
        labels = [str(labels)]

    # 自动确保 labels 存在（避免 422）
    _ensure_labels(owner, repo, labels, token)

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    payload = {
        "title": str(title),
        "body": body or "",
    }

    # assignee：尽量别强制指定（很多人没配 USERNAME/或 token 权限不足）
    if assignee:
        payload["assignees"] = [str(assignee)]

    # 先带 labels 创建；若还是 422（例如 labels 权限/其它校验），再降级不带 labels 重试
    try:
        r = _request("POST", url, token, expected_status=(201,), json=payload | ({"labels": list(labels)} if labels else {}))
    except RuntimeError as e:
        msg = str(e)
        if "422" in msg and labels:
            r = _request("POST", url, token, expected_status=(201,), json=payload)
        else:
            raise

    issue_url = r.json().get("html_url", "")
    print('Successfully created Issue "%s" %s' % (title, issue_url))
    return issue_url


if __name__ == "__main__":
    make_github_issue(
        title="Test Issue",
        body="Hello from DailyPapers",
        labels=["DailyPapers"],
    )
