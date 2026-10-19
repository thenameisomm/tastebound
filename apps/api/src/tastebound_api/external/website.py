from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from bs4 import BeautifulSoup

from tastebound_api.errors import AppError

MAX_PAGES = 3
MAX_BYTES_PER_PAGE = 1_500_000
MAX_REDIRECTS = 3
MAX_TEXT_CHARS = 12_000
USER_AGENT = "TasteBoundBot/0.1 (+https://github.com/tastebound; hackathon demo)"

INTERESTING_LINK = (
    "see",
    "do",
    "eat",
    "drink",
    "culture",
    "event",
    "visit",
    "experience",
    "attraction",
    "neighbourhood",
    "neighborhood",
)


class UrlNotAllowed(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__("url_not_allowed", 422, "URL not allowed", detail)


class WebsiteUnreadable(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__("website_unreadable", 422, "Website unreadable", detail)


@dataclass
class SiteText:
    url: str
    title: str
    text: str
    pages: list[str] = field(default_factory=list)
    chars: int = 0


def _host_is_public(host: str) -> tuple[bool, str]:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, "The hostname could not be resolved."
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False, f"Address {address} is not a public address."
        if str(ip) == "169.254.169.254":
            return False, "Metadata endpoints are blocked."
    return True, ""


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UrlNotAllowed("Only http(s) URLs are allowed.")
    if not parsed.hostname:
        raise UrlNotAllowed("The URL has no hostname.")
    allowed, reason = _host_is_public(parsed.hostname)
    if not allowed:
        raise UrlNotAllowed(reason)
    return url


async def _fetch_html(client: httpx.AsyncClient, url: str) -> httpx.Response:
    response = await client.get(url, headers={"User-Agent": USER_AGENT})
    if response.status_code in {301, 302, 303, 307, 308}:
        return response
    if len(response.content) > MAX_BYTES_PER_PAGE:
        raise WebsiteUnreadable("The page is larger than 1.5 MB.")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise WebsiteUnreadable("The page is not HTML.")
    return response


async def _allowed_by_robots(client: httpx.AsyncClient, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
        if response.status_code >= 400:
            return True
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except httpx.HTTPError:
        return True


def _extract(html: str, url: str) -> tuple[str, str, list[tuple[str, str]]]:
    title = ""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    text = trafilatura.extract(html, url=url) or ""
    if not text:
        text = soup.get_text(" ", strip=True)
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href"))
        label = anchor.get_text(" ", strip=True)
        links.append((href, label))
    return title, text, links


def _pick_pages(links: list[tuple[str, str]], base_url: str, domain: str) -> list[str]:
    picked: list[str] = []
    for href, label in links:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != domain:
            continue
        combined = f"{label} {parsed.path}".casefold()
        if not any(keyword in combined for keyword in INTERESTING_LINK):
            continue
        if absolute in picked or absolute == base_url:
            continue
        picked.append(absolute)
        if len(picked) >= MAX_PAGES - 1:
            break
    return picked


async def read_website(url: str, *, request_timeout: float = 12.0) -> SiteText:
    validate_public_url(url)
    domain = urlparse(url).netloc
    pages: list[str] = []
    chunks: list[str] = []
    title = ""
    async with httpx.AsyncClient(
        timeout=request_timeout,
        follow_redirects=False,
    ) as client:
        current = url
        redirects = 0
        response: httpx.Response | None = None
        while True:
            validate_public_url(current)
            response = await _fetch_html(client, current)
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    raise WebsiteUnreadable("The site redirected without a location.")
                current = urljoin(current, location)
                redirects += 1
                if redirects > MAX_REDIRECTS:
                    raise WebsiteUnreadable("Too many redirects.")
                continue
            if response.status_code >= 400:
                raise WebsiteUnreadable(f"The site returned HTTP {response.status_code}.")
            break
        if response is None:
            raise WebsiteUnreadable("The site could not be read.")
        allowed = await _allowed_by_robots(client, current)
        if not allowed:
            raise WebsiteUnreadable("robots.txt disallows reading this page.")
        title, text, links = _extract(response.text, current)
        pages.append(current)
        chunks.append(text)
        for candidate in _pick_pages(links, current, domain):
            if not await _allowed_by_robots(client, candidate):
                continue
            try:
                extra = await _fetch_html(client, candidate)
            except (httpx.HTTPError, WebsiteUnreadable):
                continue
            _, extra_text, _ = _extract(extra.text, candidate)
            pages.append(candidate)
            chunks.append(extra_text)
            if len(" ".join(chunks)) >= MAX_TEXT_CHARS:
                break
    combined = "\n\n".join(chunk for chunk in chunks if chunk).strip()
    combined = combined[:MAX_TEXT_CHARS]
    return SiteText(url=url, title=title, text=combined, pages=pages, chars=len(combined))
