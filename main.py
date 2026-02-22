name: daily alerts

on:
  push:
    branches: [ "main" ]
  schedule:
    - cron: "10 20 * * 1,2,3,4,5,6"
  workflow_dispatch: {}

# 关键：否则默认 token 可能没有写权限，导致 push/建 issue 失败
permissions:
  contents: write
  issues: write

jobs:
  daily:
    runs-on: ubuntu-latest
    timeout-minutes: 25

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run DailyPapers
        env:
          # GitHub token：优先用你自己建的 GH_TOKEN（可选），否则用 Actions 自带 github.token
          GH_TOKEN: ${{ secrets.GH_TOKEN || github.token }}

          # repo 信息：强烈建议显式传，避免 config 里写死
          REPO_OWNER: ${{ github.repository_owner }}
          REPO_NAME: ${{ github.event.repository.name }}

          # 关键词 & OpenAI：不想改 config.py 就在这里配（推荐）
          # KEYWORD_LIST 支持：JSON 数组 或 逗号分隔字符串
          KEYWORD_LIST: ${{ secrets.KEYWORD_LIST }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_API_KEYS: ${{ secrets.OPENAI_API_KEYS }}
          LANGUAGE: ${{ secrets.LANGUAGE }}
        run: |
          python main.py

      - name: Commit and push changes (export/)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          if git diff --cached --quiet; then
            echo "No changes to commit."
            exit 0
          fi
          git commit -m "Automated snapshot"
          git push
