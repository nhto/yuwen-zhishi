#!/usr/bin/env python3
"""Add site portal 「返回主頁」 link to every game HTML under docs/語文知識/."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GAMES_ROOT = DOCS / "語文知識"
MARKER = "yuwen-site-portal-home"

# Slim fixed strip above game content — avoids overlapping sticky topbars / logos.
SNIPPET_TEMPLATE = """<!-- {marker} -->
<nav class="{marker}" aria-label="站點導覽">
  <a class="{marker}__link" href="{href}" aria-label="返回主頁">返回主頁</a>
</nav>
<style>
:root{{--yuwen-portal-bar-h:40px}}
.{marker}{{
  position:fixed;
  top:0;left:0;right:0;
  z-index:2147483000;
  box-sizing:border-box;
  min-height:var(--yuwen-portal-bar-h);
  padding:5px max(12px, env(safe-area-inset-right)) 5px max(12px, env(safe-area-inset-left));
  padding-top:calc(5px + env(safe-area-inset-top));
  display:flex;
  align-items:center;
  justify-content:flex-start;
  gap:8px;
  background:rgba(255,252,245,.97);
  border-bottom:2px solid rgba(59,47,47,.14);
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
}}
.{marker}__link{{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:6px 14px;
  min-height:40px;
  font-family:'Noto Sans TC','PingFang TC','Microsoft JhengHei',system-ui,sans-serif;
  font-size:14px;
  font-weight:800;
  line-height:1.2;
  text-decoration:none;
  color:#3B2F2F;
  background:#fff;
  border:2.5px solid #3B2F2F;
  border-radius:999px;
  box-shadow:0 3px 0 rgba(59,47,47,.18);
  -webkit-tap-highlight-color:transparent;
}}
.{marker}__link:focus-visible{{outline:3px solid #9B8CF5;outline-offset:2px}}
.{marker}__link:active{{transform:translateY(2px);box-shadow:0 1px 0 rgba(59,47,47,.18)}}
@media (prefers-reduced-motion:reduce){{.{marker}__link:active{{transform:none}}}}
body{{
  padding-top:calc(var(--yuwen-portal-bar-h) + env(safe-area-inset-top)) !important;
}}
body .topbar,body .bar,body .app-header,body .top,body #topbar.topbar,body header.topbar{{
  top:calc(var(--yuwen-portal-bar-h) + env(safe-area-inset-top)) !important;
}}
</style>
"""

BLOCK_RE = re.compile(
    rf"<!-- {MARKER} -->\s*.*?</style>\s*",
    re.DOTALL | re.IGNORECASE,
)


def portal_href(html_path: Path) -> str:
    rel_parent = html_path.parent.relative_to(DOCS)
    ups = len(rel_parent.parts)
    return "/".join([".."] * ups) + "/index.html"


def snippet_for(href: str) -> str:
    return SNIPPET_TEMPLATE.format(marker=MARKER, href=href)


def inject_or_fix(text: str, href: str) -> tuple[str, str]:
    """Return (new_text, action) where action is added|updated|unchanged."""
    new_snippet = snippet_for(href)

    if MARKER in text:
        if BLOCK_RE.search(text):
            new_text = BLOCK_RE.sub(new_snippet, text, count=1)
            if new_text != text:
                return new_text, "updated"
            return text, "unchanged"
        # Legacy single-line link without block wrapper — replace first marker region
        new_text, n = re.subn(
            rf'(<a class="{MARKER}" href=")[^"]*(")',
            rf'<a class="{MARKER}__link" href="{href}"',
            text,
            count=1,
        )
        if n:
            return new_text, "updated"
        return text, "unchanged"

    m = re.search(r"<body[^>]*>", text, flags=re.IGNORECASE)
    if not m:
        raise ValueError("no <body> tag")
    insert_at = m.end()
    new_text = text[:insert_at] + "\n" + new_snippet + text[insert_at:]
    return new_text, "added"


def main() -> None:
    files = sorted(GAMES_ROOT.rglob("*.html"))
    if not files:
        raise SystemExit(f"No HTML under {GAMES_ROOT}")

    stats: dict[str, int] = {}
    samples: dict[int, list[str]] = {}

    for path in files:
        href = portal_href(path)
        depth = len(path.parent.relative_to(DOCS).parts)
        samples.setdefault(depth, []).append(f"{path.relative_to(ROOT)} -> {href}")

        original = path.read_text(encoding="utf-8")
        new_text, action = inject_or_fix(original, href)
        stats[action] = stats.get(action, 0) + 1
        if new_text != original:
            path.write_text(new_text, encoding="utf-8")

    print(f"Processed {len(files)} files")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print("Sample hrefs by depth (parent segments under docs/):")
    for depth in sorted(samples):
        ex = samples[depth][0]
        print(f"  depth {depth}: {ex}")


if __name__ == "__main__":
    main()
