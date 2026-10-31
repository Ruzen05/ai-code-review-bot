from types import SimpleNamespace

import review_bot


def fake_client(reply_text: str):
    """Minimal stand-in for anthropic.Anthropic() returning a fixed reply."""
    def create(**kwargs):
        return SimpleNamespace(content=[SimpleNamespace(text=reply_text)])
    return SimpleNamespace(messages=SimpleNamespace(create=create))


def test_annotate_numbers_added_and_context_lines():
    patch = "@@ -1,3 +1,4 @@\n import os\n-x = 1\n+x = 2\n+y = 3\n print(x)"
    text, valid = review_bot.annotate_patch(patch)
    assert valid == {1, 2, 3, 4}
    assert "    2 +x = 2" in text
    assert "    3 +y = 3" in text


def test_annotate_removed_lines_get_no_number():
    patch = "@@ -5,2 +5,1 @@\n-old line\n keep"
    text, valid = review_bot.annotate_patch(patch)
    assert valid == {5}
    assert "      -old line" in text


def test_annotate_handles_multiple_hunks():
    patch = "@@ -1,1 +1,2 @@\n a\n+b\n@@ -20,1 +21,2 @@\n c\n+d"
    _, valid = review_bot.annotate_patch(patch)
    assert valid == {1, 2, 21, 22}


def test_review_file_parses_plain_json():
    reply = '{"findings": [{"line": 3, "severity": "high", "comment": "bug"}]}'
    findings = review_bot.review_file(fake_client(reply), "a.py", "diff")
    assert findings == [{"line": 3, "severity": "high", "comment": "bug"}]


def test_review_file_strips_code_fences():
    reply = '```json\n{"findings": [{"line": 1, "severity": "low", "comment": "x"}]}\n```'
    findings = review_bot.review_file(fake_client(reply), "a.py", "diff")
    assert len(findings) == 1 and findings[0]["line"] == 1


def test_review_file_returns_empty_on_garbage():
    assert review_bot.review_file(fake_client("not json at all"), "a.py", "diff") == []
