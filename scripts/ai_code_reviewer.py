#!/usr/bin/env python3
"""
AI Code Reviewer using Gemini API
Analyzes code changes and posts review comments to GitHub Pull Requests

Version: 1.0.0
"""

import os
import json
import sys
from typing import Dict, List, Optional
import google.generativeai as genai
import requests


class AICodeReviewer:
    """AI-powered code reviewer using Gemini API"""

    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.pr_number = os.getenv("PR_NUMBER")
        self.repo_name = os.getenv("REPO_NAME")

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not self.pr_number:
            raise ValueError("PR_NUMBER environment variable is required")
        if not self.repo_name:
            raise ValueError("REPO_NAME environment variable is required")

        # Configure Gemini API
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def read_diff_file(self, filepath: str = "changes.diff") -> str:
        """Read the git diff file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: {filepath} not found")
            return ""

    def read_changed_files(self, filepath: str = "changed_files.txt") -> List[str]:
        """Read the list of changed files"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: {filepath} not found")
            return []

    def analyze_code_with_gemini(self, diff: str, changed_files: List[str]) -> Dict:
        """Analyze code changes using Gemini API"""

        files_list = "\n".join(f"- {f}" for f in changed_files)

        prompt = f"""あなたは経験豊富なコードレビュアーです。以下のコード変更をレビューしてください。

変更されたファイル:
{files_list}

コード差分:
```diff
{diff}
```

以下の観点でレビューを行い、重要な問題のみを指摘してください：

1. **バグの可能性**: ロジックエラー、エッジケースの未処理、null/undefined参照など
2. **セキュリティ脆弱性**: インジェクション、認証・認可の問題、機密情報の露出など
3. **パフォーマンス問題**: 非効率なアルゴリズム、不要な計算、メモリリークなど
4. **コードの可読性・保守性**: 命名規則、コードの複雑さ、重複コードなど
5. **ベストプラクティス**: 言語固有の慣習、設計パターン、エラーハンドリングなど

レビュー結果は以下のJSON形式で返してください：

```json
{{
  "summary": {{
    "total_issues": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0
  }},
  "issues": [
    {{
      "file": "ファイルパス",
      "severity": "high|medium|low",
      "category": "bug|security|performance|readability|best-practice",
      "title": "問題のタイトル",
      "description": "詳細な説明",
      "suggestion": "改善提案",
      "line_range": "行番号（オプション）"
    }}
  ],
  "overall_comment": "全体的な評価コメント"
}}
```

軽微な問題やスタイルの好みの問題は指摘せず、実質的に重要な問題のみを報告してください。
問題がない場合は、issues配列を空にして、overall_commentでポジティブなフィードバックを提供してください。

JSON形式のみを返してください。説明文や追加のテキストは不要です。"""

        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Extract JSON from response
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Try to parse JSON
            try:
                review_result = json.loads(response_text)
                return review_result
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    review_result = json.loads(json_str)
                    return review_result
                else:
                    print("Warning: Could not find JSON in Gemini response")
                    return self._create_fallback_response(response_text)

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._create_error_response(str(e))

    def _create_fallback_response(self, text: str) -> Dict:
        """Create a fallback response when JSON parsing fails"""
        return {
            "summary": {
                "total_issues": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            },
            "issues": [],
            "overall_comment": text[:500]  # Truncate if too long
        }

    def _create_error_response(self, error: str) -> Dict:
        """Create an error response"""
        return {
            "summary": {
                "total_issues": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            },
            "issues": [],
            "overall_comment": f"レビュー中にエラーが発生しました: {error}"
        }

    def format_review_as_markdown(self, review: Dict) -> str:
        """Format review results as markdown"""

        severity_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵"
        }

        category_emoji = {
            "bug": "🐛",
            "security": "🔒",
            "performance": "⚡",
            "readability": "📖",
            "best-practice": "✨"
        }

        markdown = "## 🤖 AI Code Review\n\n"

        # Summary
        summary = review.get("summary", {})
        markdown += "### 📊 Summary\n\n"
        markdown += f"- **Total Issues**: {summary.get('total_issues', 0)}\n"
        markdown += f"- 🔴 High Severity: {summary.get('high_severity', 0)}\n"
        markdown += f"- 🟡 Medium Severity: {summary.get('medium_severity', 0)}\n"
        markdown += f"- 🔵 Low Severity: {summary.get('low_severity', 0)}\n\n"

        # Issues
        issues = review.get("issues", [])
        if issues:
            markdown += "### 🔍 Findings\n\n"
            for idx, issue in enumerate(issues, 1):
                severity = issue.get("severity", "low")
                category = issue.get("category", "best-practice")

                markdown += f"#### {idx}. {severity_emoji.get(severity, '⚪')} {category_emoji.get(category, '📝')} {issue.get('title', 'Issue')}\n\n"
                markdown += f"**File**: `{issue.get('file', 'Unknown')}`\n\n"

                if issue.get('line_range'):
                    markdown += f"**Line**: {issue.get('line_range')}\n\n"

                markdown += f"**Severity**: {severity.capitalize()}\n\n"
                markdown += f"**Category**: {category}\n\n"
                markdown += f"**Description**: {issue.get('description', '')}\n\n"

                if issue.get('suggestion'):
                    markdown += f"**Suggestion**: {issue.get('suggestion', '')}\n\n"

                markdown += "---\n\n"

        # Overall comment
        overall = review.get("overall_comment", "")
        if overall:
            markdown += "### 💬 Overall Assessment\n\n"
            markdown += f"{overall}\n\n"

        markdown += "---\n"
        markdown += "*Powered by Google Gemini API (gemini-2.0-flash-exp)*\n"

        return markdown

    def post_comment_to_github(self, comment: str) -> bool:
        """Post review comment to GitHub PR"""

        url = f"https://api.github.com/repos/{self.repo_name}/issues/{self.pr_number}/comments"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "body": comment
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print(f"Successfully posted comment to PR #{self.pr_number}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error posting comment to GitHub: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False

    def save_results(self, review: Dict, markdown: str):
        """Save review results to files"""

        # Save JSON
        with open("review_results.json", "w", encoding="utf-8") as f:
            json.dump(review, f, indent=2, ensure_ascii=False)

        # Save Markdown
        with open("review_results.md", "w", encoding="utf-8") as f:
            f.write(markdown)

        print("Review results saved to review_results.json and review_results.md")

    def run(self):
        """Main execution flow"""

        print("🤖 AI Code Reviewer Starting...")
        print(f"Repository: {self.repo_name}")
        print(f"PR Number: {self.pr_number}")

        # Read diff and changed files
        diff = self.read_diff_file()
        changed_files = self.read_changed_files()

        if not diff:
            print("No diff found. Skipping review.")
            return

        if not changed_files:
            print("No changed files found. Skipping review.")
            return

        print(f"\nAnalyzing {len(changed_files)} changed file(s)...")

        # Analyze with Gemini
        review_result = self.analyze_code_with_gemini(diff, changed_files)

        # Format as markdown
        markdown_comment = self.format_review_as_markdown(review_result)

        # Save results
        self.save_results(review_result, markdown_comment)

        # Post to GitHub
        success = self.post_comment_to_github(markdown_comment)

        if success:
            print("\n✅ AI Code Review completed successfully!")
        else:
            print("\n⚠️ AI Code Review completed but failed to post comment")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        reviewer = AICodeReviewer()
        reviewer.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
