#!/usr/bin/env python3
"""Convert MediaWiki source files to Markdown for GitHub Pages/MkDocs.

- Source:   mediawiki/*.mediawiki  (canonical content, edited by hand)
- Output:   docs/<same_name>.md    (generated, overwritten on each run)

The goal is to keep structure and formatting as close as possible to MediaWiki,
including headings, links, images, and galleries.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable
import urllib.parse
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
MEDIAWIKI_DIR = ROOT / "mediawiki"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
MEDIAWIKI_BASE_URL = "https://wiki.wega-project.ru/wiki/index.php"
MEDIAWIKI_FILE_URL = "https://wiki.wega-project.ru/wiki/images"
DEFAULT_PAGES_FILE = ROOT / "all_pages.txt"
INVALID_FILENAME_CHARS = '/<>:"|?*'


_HEADING_PATTERN = re.compile(r"^(={1,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
_EXT_LINK_PATTERN = re.compile(r"\[(https?://[^\s\]]+)(?:\s+([^\]]+))?\]")
_INT_LINK_PATTERN = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")


def sanitize_title_to_filename(title: str) -> str:
    """Convert a MediaWiki page title into a safe filename.

    Rules mirror the shell script from MIGRATION_GUIDE:
    - Spaces are normalized to underscores.
    - Characters / < > : " | ? * are replaced with underscores.
    """

    base = title.replace(" ", "_")
    for ch in INVALID_FILENAME_CHARS:
        base = base.replace(ch, "_")
    return base


def convert_headings(text: str) -> str:
    """Convert MediaWiki headings (= H1 =, == H2 ==) to Markdown (# H1, ## H2)."""

    def _repl(match: re.Match[str]) -> str:
        equals = match.group(1)
        title = match.group(2).strip()
        hashes = "#" * len(equals)
        return f"{hashes} {title}"

    return _HEADING_PATTERN.sub(_repl, text)


def convert_emphasis(text: str) -> str:
    """Convert '''bold''' and ''italic'' to Markdown **bold** / *italic*.

    Order matters: bold+italic → bold → italic.
    """

    # bold+italic: '''''text'''''
    text = re.sub(r"'''''(.*?)'''''", r"***\1***", text, flags=re.DOTALL)
    # bold: '''text'''
    text = re.sub(r"'''(.*?)'''", r"**\1**", text, flags=re.DOTALL)
    # italic: ''text''
    text = re.sub(r"''(.*?)''", r"*\1*", text, flags=re.DOTALL)
    return text


def convert_external_links(text: str) -> str:
    """Convert [https://example.com Label] to [Label](https://example.com).

    Bare URLs (https://...) are left as-is and will usually render as links.
    """

    def _repl(match: re.Match[str]) -> str:
        url = match.group(1).strip()
        label = (match.group(2) or "").strip() or url
        return f"[{label}]({url})"

    return _EXT_LINK_PATTERN.sub(_repl, text)


def _is_file_link_target(target: str) -> bool:
    lower = target.lower()
    return lower.startswith("файл:") or lower.startswith("file:")


def convert_internal_links(text: str) -> str:
    """Convert [[Page]] / [[Page|Label]] and [[Файл:img.png|...]]."""

    def _repl(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or "").strip()

        # File / image links
        if _is_file_link_target(target):
            rest = target.split(":", 1)[1].strip() if ":" in target else target
            filename = rest.strip()

            alt_text = ""
            if label:
                # label can contain options separated by '|', use last part as caption
                parts = [p.strip() for p in label.split("|") if p.strip()]
                if parts:
                    alt_text = parts[-1]
            if not alt_text:
                alt_text = filename

            return f"![{alt_text}](assets/{filename})"

        # Normal internal page links
        page_name = target
        if not label:
            label = page_name
        # Use same sanitization rules as for output filenames, so links match files.
        filename_base = sanitize_title_to_filename(page_name)
        href = f"{filename_base}.md"
        return f"[{label}]({href})"

    return _INT_LINK_PATTERN.sub(_repl, text)


def _build_gallery_html(lines: Iterable[str]) -> str:
    """Build HTML gallery from lines with 'Файл:...' entries.

    Each line is expected to be in one of forms:
      - 'Файл:img.png'
      - 'Файл:img.png|caption'
      - 'Файл:img.png|опция1|...|caption'
    """

    images: list[tuple[str, str]] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not (line.startswith("Файл:") or line.startswith("File:") or line.startswith("файл:")):
            continue
        rest = line.split(":", 1)[1]
        parts = [p.strip() for p in rest.split("|")]
        if not parts:
            continue
        filename = parts[0]
        caption = parts[-1] if len(parts) > 1 else ""
        images.append((filename, caption))

    if not images:
        # Fallback: just join original lines if we couldn't parse anything useful
        return "\n".join(lines)

    out: list[str] = ["<div class=\"gallery-compact\">"]
    for filename, caption in images:
        alt = caption or filename
        out.append(f"  <img src=\"assets/{filename}\" alt=\"{alt}\" />")
    out.append("</div>")
    return "\n".join(out)


def convert_galleries(text: str) -> str:
    """Convert <gallery>...</gallery> blocks to HTML gallery-compact blocks."""

    lines = text.splitlines()
    out_lines: list[str] = []
    in_gallery = False
    gallery_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not in_gallery:
            if stripped.startswith("<gallery"):
                # Start of gallery; attributes are ignored, items will follow on next lines
                in_gallery = True
                gallery_lines = []
                continue
            out_lines.append(line)
            continue

        # Inside gallery
        if "</gallery>" in line:
            before, after = line.split("</gallery>", 1)
            if before.strip():
                gallery_lines.append(before)
            out_lines.append(_build_gallery_html(gallery_lines))
            in_gallery = False
            gallery_lines = []
            if after.strip():
                out_lines.append(after)
            continue

        gallery_lines.append(line)

    if in_gallery:
        # Unclosed gallery; try to render what we have
        out_lines.append(_build_gallery_html(gallery_lines))

    # Preserve trailing newline if it was present
    result = "\n".join(out_lines)
    if text.endswith("\n"):
        result += "\n"
    return result


def convert_tables(text: str) -> str:
    """Convert MediaWiki tables {| ... |} to Markdown tables."""

    lines = text.splitlines()
    out_lines: list[str] = []
    in_table = False
    table_rows: list[list[str]] = []
    header_row: list[str] = []
    current_row: list[str] = []
    in_header = False
    
    for line in lines:
        stripped = line.strip()
        
        if not in_table:
            # Check for table start
            if stripped.startswith("{|"):
                in_table = True
                table_rows = []
                header_row = []
                current_row = []
                in_header = False
                continue
            out_lines.append(line)
            continue
        
        # Inside table
        if stripped.startswith("|}"):
            # End of table - convert to markdown
            if current_row:
                if in_header:
                    header_row.extend(current_row)
                else:
                    table_rows.append(current_row)
            
            if header_row or table_rows:
                # Build markdown table
                md_table = _build_markdown_table(header_row, table_rows)
                out_lines.extend(md_table)
            
            in_table = False
            header_row = []
            table_rows = []
            current_row = []
            in_header = False
            continue
        
        # Skip table attributes and caption
        if stripped.startswith("|+") or (stripped.startswith("class=") and "=" in stripped) or not stripped:
            continue
        
        # Header cells
        if stripped.startswith("!"):
            # If we were building a data row, save it first
            if current_row and not in_header:
                table_rows.append(current_row)
                current_row = []
            
            in_header = True
            # Remove leading ! and add to header - keep empty cells
            cell_content = stripped[1:].strip()
            current_row.append(cell_content)
            continue
        
        # Row separator
        if stripped.startswith("|-"):
            # Save current row
            if current_row:
                if in_header:
                    header_row.extend(current_row)
                    in_header = False
                else:
                    table_rows.append(current_row)
                current_row = []
            continue
        
        # Data cell
        if stripped.startswith("|") and not stripped.startswith("|}"):
            # If we were in header mode, switch to data mode
            if in_header and current_row:
                header_row.extend(current_row)
                current_row = []
                in_header = False
            
            # Remove leading | - keep empty cells as empty strings
            cell_content = stripped[1:].strip()
            current_row.append(cell_content)
            continue
    
    # Handle unclosed table
    if in_table:
        if current_row:
            if in_header:
                header_row.extend(current_row)
            else:
                table_rows.append(current_row)
        if header_row or table_rows:
            md_table = _build_markdown_table(header_row, table_rows)
            out_lines.extend(md_table)
    
    result = "\n".join(out_lines)
    if text.endswith("\n"):
        result += "\n"
    return result


def _build_markdown_table(header: list[str], rows: list[list[str]]) -> list[str]:
    """Build a markdown table from header and rows."""
    
    if not header and not rows:
        return []
    
    # If no explicit header, use first row as header
    if not header and rows:
        header = rows[0]
        rows = rows[1:]
    
    # Determine number of columns
    max_cols = len(header) if header else max((len(r) for r in rows), default=0)
    
    if max_cols == 0:
        return []
    
    # Normalize header
    if len(header) < max_cols:
        header.extend([""] * (max_cols - len(header)))
    elif len(header) > max_cols:
        header = header[:max_cols]
    
    # Normalize rows
    normalized_rows = []
    for row in rows:
        if len(row) < max_cols:
            row = row + [""] * (max_cols - len(row))
        elif len(row) > max_cols:
            row = row[:max_cols]
        normalized_rows.append(row)
    
    # Build markdown
    result = []
    
    # Header
    result.append("| " + " | ".join(header) + " |")
    
    # Separator
    result.append("| " + " | ".join(["---"] * max_cols) + " |")
    
    # Rows
    for row in normalized_rows:
        result.append("| " + " | ".join(row) + " |")
    
    return result


def remove_category_links(text: str) -> str:
    """Remove MediaWiki category links [[Категория:...]] or [[Category:...]]."""
    
    # Remove category links
    text = re.sub(r'\[\[(?:Категория|Category|категория|category):([^\]]+)\]\]', '', text, flags=re.IGNORECASE)
    return text


def convert_lists(text: str) -> str:
    """Convert MediaWiki lists (* and #) to Markdown lists."""
    
    lines = text.splitlines()
    result = []
    
    for line in lines:
        # Skip if line is already a markdown heading (starts with # followed by space)
        if line.startswith('#') and len(line) > 1 and line[1] == ' ':
            result.append(line)
            continue
        
        # Check if line starts with list markers
        if line.startswith('*'):
            # Unordered list
            count = 0
            for char in line:
                if char == '*':
                    count += 1
                else:
                    break
            content = line[count:].strip()
            indent = '  ' * (count - 1)
            result.append(f"{indent}- {content}")
        elif line.startswith('#') and (len(line) < 2 or line[1] != ' '):
            # Ordered list (not a markdown heading)
            count = 0
            for char in line:
                if char == '#':
                    count += 1
                else:
                    break
            content = line[count:].strip()
            indent = '  ' * (count - 1)
            result.append(f"{indent}1. {content}")
        else:
            result.append(line)
    
    return '\n'.join(result)


def convert_text(text: str) -> str:
    """Run all conversions on a single MediaWiki source string."""

    # Order matters: tables and galleries first (they do not use [[...]]), then formatting/links.
    text = convert_tables(text)
    text = convert_galleries(text)
    text = remove_category_links(text)
    text = convert_lists(text)  # Before headings to avoid confusion with ##
    text = convert_headings(text)
    text = convert_emphasis(text)
    text = convert_external_links(text)
    text = convert_internal_links(text)
    return text


def convert_file(src: Path) -> str:
    raw = src.read_text(encoding="utf-8", errors="ignore")
    return convert_text(raw)


def _load_remote_titles(pages_file: Path) -> list[str]:
    """Load page titles for remote mode from a file like all_pages.txt."""

    titles: list[str] = []
    if not pages_file.exists():
        raise FileNotFoundError(pages_file)
    text = pages_file.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        titles.append(t)
    return titles


def fetch_page_raw(title: str) -> str:
    """Fetch raw MediaWiki source for a single page title from the live wiki."""

    encoded = urllib.parse.quote(title)
    url = f"{MEDIAWIKI_BASE_URL}?title={encoded}&action=raw"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP error {e.code} while fetching {title!r} from {url}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Network error while fetching {title!r} from {url}: {e}"
        ) from e
    return data.decode("utf-8", errors="ignore")


def fetch_all_pages_from_api() -> list[str]:
    """Fetch list of all pages from MediaWiki API (excluding redirects)."""
    
    import json
    
    pages = []
    apcontinue = None
    
    while True:
        # Build API URL - exclude redirects
        params = {
            "action": "query",
            "list": "allpages",
            "apfilterredir": "nonredirects",
            "aplimit": "500",
            "format": "json",
        }
        
        if apcontinue:
            params["apcontinue"] = apcontinue
        
        query_string = urllib.parse.urlencode(params)
        api_url = f"{MEDIAWIKI_BASE_URL.rsplit('/', 1)[0]}/api.php?{query_string}"
        
        try:
            with urllib.request.urlopen(api_url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            # Extract page titles
            if "query" in data and "allpages" in data["query"]:
                for page in data["query"]["allpages"]:
                    title = page.get("title", "")
                    if title:
                        pages.append(title)
            
            # Check if there are more pages
            if "continue" in data and "apcontinue" in data["continue"]:
                apcontinue = data["continue"]["apcontinue"]
            else:
                break
                
        except Exception as e:
            print(f"Error fetching page list from API: {e}")
            break
    
    return pages


def fetch_redirects_from_api() -> dict[str, str]:
    """Fetch all redirects from MediaWiki API. Returns dict of {redirect_title: target_title}."""
    
    import json
    
    redirects = {}
    apcontinue = None
    
    while True:
        # Build API URL - only redirects
        params = {
            "action": "query",
            "list": "allpages",
            "apfilterredir": "redirects",
            "aplimit": "500",
            "format": "json",
        }
        
        if apcontinue:
            params["apcontinue"] = apcontinue
        
        query_string = urllib.parse.urlencode(params)
        api_url = f"{MEDIAWIKI_BASE_URL.rsplit('/', 1)[0]}/api.php?{query_string}"
        
        try:
            with urllib.request.urlopen(api_url, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            # Extract redirect titles
            if "query" in data and "allpages" in data["query"]:
                for page in data["query"]["allpages"]:
                    title = page.get("title", "")
                    if title:
                        # Get redirect target
                        target = get_redirect_target(title)
                        if target:
                            redirects[title] = target
            
            # Check if there are more pages
            if "continue" in data and "apcontinue" in data["continue"]:
                apcontinue = data["continue"]["apcontinue"]
            else:
                break
                
        except Exception as e:
            print(f"Error fetching redirects from API: {e}")
            break
    
    return redirects


def get_redirect_target(title: str) -> str | None:
    """Get the target page for a redirect."""
    
    import json
    
    params = {
        "action": "query",
        "titles": title,
        "redirects": "1",
        "format": "json",
    }
    
    query_string = urllib.parse.urlencode(params)
    api_url = f"{MEDIAWIKI_BASE_URL.rsplit('/', 1)[0]}/api.php?{query_string}"
    
    try:
        with urllib.request.urlopen(api_url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        # Check for redirects in response
        if "query" in data and "redirects" in data["query"]:
            redirects_list = data["query"]["redirects"]
            if redirects_list and len(redirects_list) > 0:
                return redirects_list[0].get("to")
        
        return None
        
    except Exception:
        return None


def extract_image_filenames(text: str) -> set[str]:
    """Extract all image filenames from MediaWiki text."""
    
    images: set[str] = set()
    
    # Find [[Файл:...]] and [[File:...]] links
    for match in _INT_LINK_PATTERN.finditer(text):
        target = match.group(1).strip()
        if _is_file_link_target(target):
            rest = target.split(":", 1)[1].strip() if ":" in target else target
            filename = rest.strip()
            images.add(filename)
    
    # Find images in <gallery> tags
    lines = text.splitlines()
    in_gallery = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("<gallery"):
            in_gallery = True
            continue
        
        if "</gallery>" in line:
            in_gallery = False
            continue
        
        if in_gallery and stripped:
            if stripped.lower().startswith(("файл:", "file:")):
                rest = stripped.split(":", 1)[1]
                parts = [p.strip() for p in rest.split("|")]
                if parts:
                    images.add(parts[0])
    
    return images


def get_image_url_from_api(filename: str) -> str | None:
    """Get the actual image URL from MediaWiki API."""
    
    import json
    
    # Construct API query
    title = f"File:{filename}"
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }
    
    query_string = urllib.parse.urlencode(params)
    api_url = f"{MEDIAWIKI_BASE_URL.rsplit('/', 1)[0]}/api.php?{query_string}"
    
    try:
        with urllib.request.urlopen(api_url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        # Extract image URL from response
        if "query" in data and "pages" in data["query"]:
            for page in data["query"]["pages"].values():
                if "imageinfo" in page and len(page["imageinfo"]) > 0:
                    return page["imageinfo"][0].get("url")
        
        return None
        
    except Exception:
        return None


def download_image(filename: str, assets_dir: Path, dry_run: bool = False) -> bool:
    """Download a single image from MediaWiki to assets directory."""
    
    # Skip if already exists
    dest_path = assets_dir / filename
    if dest_path.exists():
        return True
    
    if dry_run:
        print(f"  [DRY RUN] Would download: {filename}")
        return True
    
    # Get actual URL from API
    url = get_image_url_from_api(filename)
    
    if not url:
        print(f"  Failed to get URL for {filename}")
        return False
    
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
        
        assets_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)
        print(f"  Downloaded: {filename}")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"  Failed to download {filename}: HTTP {e.code}")
        return False
    except urllib.error.URLError as e:
        print(f"  Failed to download {filename}: {e}")
        return False
    except Exception as e:
        print(f"  Failed to download {filename}: {e}")
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert MediaWiki sources to Markdown files in docs/. "
            "By default reads from local mediawiki/, or with --remote "
            "downloads raw pages from the live wiki."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        help=(
            "When using local mode: optional path to a single .mediawiki file. "
            "When using --remote: optional single page title to fetch."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output .md path when converting a single local file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write files, only show what would be done",
    )

    parser.add_argument(
        "--remote",
        action="store_true",
        help=(
            "Fetch raw page content directly from wiki.wega-project.ru "
            "instead of reading local mediawiki/*.mediawiki."
        ),
    )

    parser.add_argument(
        "--pages-file",
        type=str,
        default=str(DEFAULT_PAGES_FILE),
        help=(
            "File with page titles (one per line) to use in --remote mode. "
            "Default: all_pages.txt in repo root."
        ),
    )

    args = parser.parse_args(argv)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Remote mode: fetch raw content from live MediaWiki
    if args.remote:
        pages: list[str]
        if args.input:
            pages = [args.input.strip()]
        else:
            # Try to load from file first, if not found - fetch from API
            pages_file = Path(args.pages_file).resolve()
            if pages_file.exists():
                try:
                    pages = _load_remote_titles(pages_file)
                except Exception as e:
                    print(f"Error loading pages file: {e}")
                    print("Fetching page list from MediaWiki API...")
                    pages = fetch_all_pages_from_api()
            else:
                print("No pages file found, fetching page list from MediaWiki API...")
                pages = fetch_all_pages_from_api()

        if not pages:
            print("No page titles found to convert in remote mode.")
            return 0

        # Fetch and create redirects
        print("Fetching redirects...")
        redirects = fetch_redirects_from_api()
        if redirects:
            print(f"Found {len(redirects)} redirect(s)")
            for redirect_title, target_title in redirects.items():
                base_name = sanitize_title_to_filename(redirect_title)
                target_name = sanitize_title_to_filename(target_title)
                dst = DOCS_DIR / f"{base_name}.md"
                
                # Create redirect file with meta refresh
                redirect_content = f"---\nredirect_to: {target_name}.md\n---\n\n[Redirected to {target_title}]({target_name}.md)\n"
                
                if args.dry_run:
                    print(f"[DRY RUN][redirect] {redirect_title!r} -> {target_name}.md")
                else:
                    dst.write_text(redirect_content, encoding="utf-8")
                    print(f"Created redirect {redirect_title!r} -> {target_title!r}")

        for title in pages:
            if not title:
                continue
            try:
                raw = fetch_page_raw(title)
            except Exception as e:  # noqa: BLE001 - log and continue
                print(f"Failed to fetch {title!r}: {e}")
                continue

            # Extract and download images
            images = extract_image_filenames(raw)
            if images:
                if args.dry_run:
                    print(f"Found {len(images)} image(s) in {title!r}:")
                    for img in images:
                        print(f"  - {img}")
                else:
                    print(f"Found {len(images)} image(s) in {title!r}")
                    for img in images:
                        download_image(img, ASSETS_DIR, args.dry_run)

            md_text = convert_text(raw)
            base_name = sanitize_title_to_filename(title)
            dst = DOCS_DIR / f"{base_name}.md"

            if args.dry_run:
                print(f"[DRY RUN][remote] {title!r} -> {dst.relative_to(ROOT)}")
                continue

            dst.write_text(md_text, encoding="utf-8")
            print(f"Converted remote page {title!r} -> {dst.relative_to(ROOT)}")

        return 0

    # Local mode: use mediawiki/*.mediawiki as source
    if not MEDIAWIKI_DIR.exists():
        print(f"mediawiki directory not found at {MEDIAWIKI_DIR}")
        return 1

    if args.input:
        src_paths = [Path(args.input).resolve()]
    else:
        src_paths = sorted(MEDIAWIKI_DIR.glob("*.mediawiki"))

    if not src_paths:
        print("No .mediawiki files found to convert.")
        return 0

    for src in src_paths:
        if not src.is_file():
            continue

        # Read source and extract images
        raw = src.read_text(encoding="utf-8", errors="ignore")
        images = extract_image_filenames(raw)
        if images:
            if args.dry_run:
                print(f"Found {len(images)} image(s) in {src.name}:")
                for img in images:
                    print(f"  - {img}")
            else:
                print(f"Found {len(images)} image(s) in {src.name}")
                for img in images:
                    download_image(img, ASSETS_DIR, args.dry_run)

        # Determine output path
        base_name = src.stem
        if args.output and len(src_paths) == 1:
            dst = Path(args.output).resolve()
        else:
            dst = DOCS_DIR / f"{base_name}.md"

        md_text = convert_text(raw)

        if args.dry_run:
            src_rel = src.relative_to(ROOT) if src.is_relative_to(ROOT) else src
            dst_rel = dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst
            print(f"[DRY RUN] {src_rel} -> {dst_rel}")
            continue

        dst.write_text(md_text, encoding="utf-8")
        src_rel = src.relative_to(ROOT) if src.is_relative_to(ROOT) else src
        dst_rel = dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst
        print(f"Converted {src_rel} -> {dst_rel}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
