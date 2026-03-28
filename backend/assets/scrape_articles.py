"""
Scrape referenced articles from a Huberman Lab episode page.

Usage:
    python scrape_articles.py <huberman_episode_url>

Example:
    python scrape_articles.py https://www.hubermanlab.com/episode/improve-lymphatic-system-health-appearance

This will:
  1. Fetch the episode page and extract all article links from the "Articles" section.
  2. For each article, attempt to scrape the full text content.
  3. For paywalled articles (403), fall back to CrossRef API for abstract.
  4. Save each article as an .md file in ./articles/
"""

import sys
import os
import re
import time
import httpx
from urllib.parse import urlparse
from html.parser import HTMLParser


# ---------------------------------------------------------------------------
# Minimal HTML-to-Markdown converter (no external deps)
# ---------------------------------------------------------------------------

class _HTMLToMarkdown(HTMLParser):
    """Very small HTML→Markdown converter focused on article body text."""

    BLOCK_TAGS = {
        "p", "div", "section", "article", "main",
        "blockquote", "li", "tr", "figcaption", "pre",
    }
    SKIP_TAGS = {
        "script", "style", "nav", "footer", "header", "noscript",
        "svg", "form", "button", "iframe", "aside", "menu",
    }

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        tag = tag.lower()
        self._tag_stack.append(tag)
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self._parts.append("\n\n" + "#" * level + " ")
        elif tag == "br":
            self._parts.append("\n")
        elif tag in self.BLOCK_TAGS:
            self._parts.append("\n\n")
        elif tag == "a":
            href = dict(attrs).get("href", "")
            self._parts.append("[")
            self._tag_stack[-1] = ("a", href)
        elif tag in ("strong", "b"):
            self._parts.append("**")
        elif tag in ("em", "i"):
            self._parts.append("*")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if self._skip_depth:
            if self._tag_stack:
                self._tag_stack.pop()
            return
        if not self._tag_stack:
            return
        top = self._tag_stack.pop()
        if isinstance(top, tuple) and top[0] == "a":
            href = top[1]
            self._parts.append(f"]({href})")
        elif tag_lower in ("strong", "b"):
            self._parts.append("**")
        elif tag_lower in ("em", "i"):
            self._parts.append("*")
        elif tag_lower in self.BLOCK_TAGS or tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._parts.append("\n\n")

    def handle_data(self, data: str):
        if self._skip_depth:
            return
        self._parts.append(data)

    def get_markdown(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_markdown(html: str) -> str:
    parser = _HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


# ---------------------------------------------------------------------------
# Post-processing: strip reference noise from scraped article markdown
# ---------------------------------------------------------------------------

def clean_article_content(md: str) -> str:
    """Strip out reference/citation noise and keep only core article text."""

    # Remove [Google Scholar](…) and [Crossref](…) links (with optional brackets)
    md = re.sub(r"\[?\[Google Scholar\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[Crossref\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[PubMed\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[Abstract\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[Full Text\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[PDF\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[Web of Science\]\]\([^)]*\)\]?", "", md)
    md = re.sub(r"\[?\[Medline\]\]\([^)]*\)\]?", "", md)

    # Remove empty markdown links: []() or [](some_url)
    md = re.sub(r"\[\s*\]\([^)]*\)", "", md)

    # Remove Google Scholar links with any anchor text
    md = re.sub(r"\[[^\]]*\]\(https?://scholar\.google\.com[^)]*\)", "", md)

    # Remove inline reference citation blocks like:
    #   Author1  A,  Author2  B.  2020..   Title. .  Journal  182::270–96
    # These have double-dots (..) and double-colons (::) as formatting artifacts
    md = re.sub(
        r"(?m)^ *[A-Z][a-z]+ +[A-Z]{1,3}(?:, +[A-Z][a-z]+ +[A-Z]{1,3})*(?:, +et al\.?)?\s+\d{4}\.\.\s+.*?(?:\n|$)",
        "",
        md,
    )

    # Remove lines that are just crossref/doi links on their own
    md = re.sub(r"(?m)^\s*https?://doi\.org/\S+\s*$", "", md)

    # Remove cookie consent / banner text patterns
    md = re.sub(r"(?i)we use cookies.*?(?:accept|dismiss|close|okay|got it)\.?", "", md, flags=re.DOTALL)
    md = re.sub(r"(?i)this site uses cookies.*?(?:\.\s|\n)", "", md, flags=re.DOTALL)

    # Remove "Sign in" / "Subscribe" / "Access" prompts
    md = re.sub(r"(?im)^.*(?:sign in|log in|subscribe|create an? (?:free )?account|institutional access).*$", "", md)

    # Remove navigation breadcrumbs (e.g., "Home > Journal > Volume")
    md = re.sub(r"(?m)^(?:Home|Skip to)\s*>.*$", "", md)

    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md.strip()


# ---------------------------------------------------------------------------
# Huberman episode page parser – extract article links
# ---------------------------------------------------------------------------

_ARTICLE_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((https?://[^)]+)\)"
)

# Domains that host academic articles
_ACADEMIC_DOMAINS = {
    "onlinelibrary.wiley.com",
    "journals.physiology.org",
    "www.sciencedirect.com",
    "www.nature.com",
    "pmc.ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "www.jneurosci.org",
    "link.springer.com",
    "www.annualreviews.org",
    "www.magonlinelibrary.com",
    "www.tandfonline.com",
    "journals.lww.com",
    "www.thoracic.theclinics.com",
    "jamanetwork.com",
    "academic.oup.com",
    "www.cell.com",
    "www.thelancet.com",
    "www.bmj.com",
    "doi.org",
}


def _is_academic_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return any(host == d or host.endswith("." + d) for d in _ACADEMIC_DOMAINS)


def extract_article_links(page_markdown: str) -> list[dict]:
    """Return list of {title, url} for academic article links on the page."""
    seen_urls: set[str] = set()
    articles: list[dict] = []
    for m in _ARTICLE_LINK_RE.finditer(page_markdown):
        title = m.group(1).strip()
        url = m.group(2).strip()
        if url in seen_urls:
            continue
        if not _is_academic_url(url):
            continue
        seen_urls.add(url)
        articles.append({"title": title, "url": url})
    return articles


# ---------------------------------------------------------------------------
# CrossRef abstract fallback for paywalled articles
# ---------------------------------------------------------------------------

def _extract_doi(url: str) -> str | None:
    """Try to extract a DOI from a URL like https://doi.org/10.xxx or .../doi/10.xxx/..."""
    # Direct doi.org link
    m = re.search(r"doi\.org/(10\.\S+)", url)
    if m:
        return m.group(1).rstrip("/")
    # Embedded in path: /doi/10.xxxx/yyyy
    m = re.search(r"/doi/(?:full/|abs/)?(10\.[^?#]+)", url)
    if m:
        return m.group(1).rstrip("/")
    # Nature: /articles/sXXXXX-XXX-XXXXX-X
    m = re.search(r"nature\.com/articles/(s\d+-\d+-\d+-\w)", url)
    if m:
        return f"10.1038/{m.group(1)}"
    # Springer: /article/10.xxxx/...
    m = re.search(r"/article/(10\.[^?#]+)", url)
    if m:
        return m.group(1).rstrip("/")
    return None


def fetch_crossref_abstract(url: str, client: httpx.Client) -> dict | None:
    """
    Query CrossRef API using the DOI extracted from the URL.
    Returns dict with 'abstract', 'authors', 'journal' or None.
    """
    doi = _extract_doi(url)
    if not doi:
        return None
    try:
        api_url = f"https://api.crossref.org/works/{doi}"
        resp = client.get(
            api_url,
            headers={"Accept": "application/json", "User-Agent": "HubermanArticleScraper/1.0 (mailto:dev@example.com)"},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("message", {})
        result = {}

        # Abstract (may contain XML/HTML tags)
        abstract = data.get("abstract", "")
        if abstract:
            # Strip JATS XML tags
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            result["abstract"] = abstract

        # Authors
        authors = data.get("author", [])
        if authors:
            names = []
            for a in authors:
                given = a.get("given", "")
                family = a.get("family", "")
                names.append(f"{given} {family}".strip())
            result["authors"] = ", ".join(names)

        # Journal
        containers = data.get("container-title", [])
        if containers:
            result["journal"] = containers[0]

        return result if result else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Article scraper
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_article(url: str, client: httpx.Client) -> tuple[str | None, str | None]:
    """
    Attempt to fetch and convert an article to markdown.
    Returns (markdown_content, error_message).
    """
    try:
        resp = client.get(url, follow_redirects=True, timeout=30)
        if resp.status_code == 403:
            return None, "Access denied (HTTP 403). Article may require institutional access."
        if resp.status_code == 451:
            return None, "Unavailable for legal reasons (HTTP 451)."
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "pdf" in content_type or url.endswith(".pdf"):
            return None, "Article is a PDF. PDF text extraction is not supported."
        md = html_to_markdown(resp.text)
        md = clean_article_content(md)
        return md, None
    except httpx.TimeoutException:
        return None, "Request timed out after 30 seconds."
    except httpx.HTTPStatusError as e:
        return None, f"HTTP error: {e.response.status_code}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _slugify(title: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:max_len].rstrip("-")


def save_article_md(
    out_dir: str,
    title: str,
    url: str,
    content: str | None,
    error: str | None,
    crossref: dict | None = None,
) -> str:
    """Write an .md file for the article and return the path."""
    filename = _slugify(title) + ".md"
    path = os.path.join(out_dir, filename)

    lines = [f"# {title}\n"]
    lines.append(f"\n**Source:** [{url}]({url})\n")

    if crossref:
        if crossref.get("journal"):
            lines.append(f"**Journal:** {crossref['journal']}\n")
        if crossref.get("authors"):
            lines.append(f"**Authors:** {crossref['authors']}\n")

    if error:
        lines.append(f"\n> ⚠️ **Could not scrape full text:** {error}\n")

    if content:
        lines.append(f"\n---\n\n{content}\n")
    elif crossref and crossref.get("abstract"):
        lines.append(f"\n---\n\n## Abstract\n\n{crossref['abstract']}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    episode_url = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(script_dir, "articles")
    os.makedirs(out_dir, exist_ok=True)

    print(f"📡  Fetching episode page: {episode_url}")
    with httpx.Client(headers=_HEADERS) as client:
        resp = client.get(episode_url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        page_md = html_to_markdown(resp.text)

    articles = extract_article_links(page_md)
    if not articles:
        print("❌  No article links found on the page.")
        sys.exit(1)

    print(f"📚  Found {len(articles)} article(s):\n")
    for i, a in enumerate(articles, 1):
        print(f"  {i:2d}. {a['title']}")
    print()

    with httpx.Client(headers=_HEADERS) as client:
        for i, article in enumerate(articles, 1):
            title = article["title"]
            url = article["url"]
            print(f"[{i}/{len(articles)}] Scraping: {title[:70]}...")

            content, error = scrape_article(url, client)

            # Fallback: get abstract from CrossRef for paywalled articles
            crossref = None
            if error:
                print(f"  ↳  Falling back to CrossRef API for abstract...")
                crossref = fetch_crossref_abstract(url, client)
                if crossref and crossref.get("abstract"):
                    print(f"  ↳  Got abstract from CrossRef ✓")
                else:
                    print(f"  ↳  No abstract available from CrossRef")

            path = save_article_md(out_dir, title, url, content, error, crossref)
            status = "✅" if content else ("📋" if crossref and crossref.get("abstract") else "⚠️")
            print(f"  {status}  → {os.path.relpath(path, script_dir)}")
            if error and not (crossref and crossref.get("abstract")):
                print(f"      {error}")

            time.sleep(0.5)

    print(f"\n🎉  Done! Articles saved to: {out_dir}")


if __name__ == "__main__":
    main()
