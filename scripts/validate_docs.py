#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

# Markdown link patterns
# For images, match until file extension + closing paren
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\((.+?\.(?:png|jpg|jpeg|gif|svg|webp|mp4))\)", re.IGNORECASE)
# For links, match non-greedy to first closing paren (good enough for most cases)
LINK_PATTERN = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")

IGNORE_SCHEMES = ("http://", "https://", "mailto:")


def is_ignored(url: str) -> bool:
    url = url.strip()
    if not url or url.startswith("#"):
        return True
    if any(url.startswith(s) for s in IGNORE_SCHEMES):
        return True
    # anchor-only or query-only
    if url.startswith("?") or url.startswith("#"):
        return True
    return False


def resolve_path(base: Path, target: str) -> Path:
    # Remove surrounding <...> if used
    t = target.strip()
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1].strip()
    # Normalize
    return (base / t).resolve()


def find_case_insensitive(p: Path) -> Path | None:
    if p.exists():
        return p
    parent = p.parent
    if not parent.exists():
        return None
    lower = p.name.lower()
    for entry in parent.iterdir():
        if entry.name.lower() == lower:
            return entry
    return None


def check_file(md: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = md.read_text(encoding="utf-8", errors="ignore")

    def _check(pattern: re.Pattern, kind: str):
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            if is_ignored(raw):
                continue
            # strip fragment/query
            path_only = raw.split("#", 1)[0].split("?", 1)[0]
            if not path_only:
                continue
            abs_path = resolve_path(md.parent, path_only)
            # Constrain to repo root to avoid escaping
            try:
                abs_path.relative_to(ROOT)
            except ValueError:
                errors.append(f"{md}: {kind} escapes repo root: {raw}")
                continue
            if not abs_path.exists():
                alt = find_case_insensitive(abs_path)
                if alt is None:
                    # Only warn for missing links, error for missing images
                    if kind == "image":
                        errors.append(f"{md}: missing {kind}: {raw} -> {abs_path.relative_to(ROOT)}")
                    else:
                        warnings.append(f"{md}: missing {kind}: {raw} -> {abs_path.relative_to(ROOT)}")
                else:
                    # Case mismatch is just a warning
                    warnings.append(
                        f"{md}: case-mismatch for {kind}: {raw} -> wanted {abs_path.name}, found {alt.name}"
                    )

    _check(IMG_PATTERN, "image")
    _check(LINK_PATTERN, "link")
    return errors, warnings


def main() -> int:
    if not DOCS_DIR.exists():
        print(f"docs directory not found at {DOCS_DIR}")
        return 1

    md_files = [p for p in DOCS_DIR.rglob("*.md") if p.is_file()]
    all_errors: list[str] = []
    all_warnings: list[str] = []
    
    for md in sorted(md_files, key=lambda p: str(p)):
        errors, warnings = check_file(md)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print(f"Found {len(all_warnings)} warning(s):")
        for w in all_warnings[:10]:  # Show first 10
            print("  ", w)
        if len(all_warnings) > 10:
            print(f"  ... and {len(all_warnings) - 10} more")

    if all_errors:
        print(f"\nFound {len(all_errors)} error(s):")
        for e in all_errors:
            print("  ", e)
        return 2

    print("\nDocumentation validation passed!")
    if all_warnings:
        print(f"({len(all_warnings)} warnings - mostly missing pages that don't exist on wiki)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
