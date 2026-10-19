from __future__ import annotations

import httpx
import pytest
import respx

from tastebound_api.external.website import (
    MAX_PAGES,
    MAX_TEXT_CHARS,
    UrlNotAllowed,
    WebsiteUnreadable,
    read_website,
)

BASE = "https://visit-lisbon.example"

PUBLIC_IP = "93.184.216.34"


@pytest.fixture(autouse=True)
def _public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    import ipaddress

    def fake_getaddrinfo(host: str, port: object, *args: object) -> list[tuple[object, ...]]:
        if host == "localhost":
            literal = "127.0.0.1"
        else:
            try:
                literal = str(ipaddress.ip_address(host))
            except ValueError:
                literal = PUBLIC_IP
        return [(2, 1, 6, "", (literal, 0))]

    monkeypatch.setattr("tastebound_api.external.website.socket.getaddrinfo", fake_getaddrinfo)


def _page(title: str, body: str, links: list[tuple[str, str]] | None = None) -> str:
    anchors = "".join(f'<a href="{href}">{label}</a>' for href, label in links or [])
    return f"<html><head><title>{title}</title></head><body><p>{body}</p>{anchors}</body></html>"


@respx.mock
async def test_reads_at_most_three_same_domain_pages() -> None:
    respx.get(f"{BASE}/robots.txt").mock(return_value=httpx.Response(404))
    respx.get(BASE).mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text=_page(
                "Visit Lisbon",
                "Fado, trams and pastel de nata.",
                [
                    (f"{BASE}/see", "See and do"),
                    (f"{BASE}/eat", "Eat and drink"),
                    (f"{BASE}/culture", "Culture"),
                    (f"{BASE}/extra", "Visit more"),
                    ("https://other.example/see", "See elsewhere"),
                ],
            ),
        )
    )
    for path in ("see", "eat", "culture"):
        respx.get(f"{BASE}/{path}").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text=_page(path.title(), f"Content for {path}."),
            )
        )

    site = await read_website(BASE)
    assert site.title == "Visit Lisbon"
    assert len(site.pages) == MAX_PAGES
    assert all(page.startswith(BASE) for page in site.pages)
    assert site.chars <= MAX_TEXT_CHARS
    assert "Fado" in site.text


@respx.mock
async def test_robots_disallow_blocks_reading() -> None:
    respx.get(f"{BASE}/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /\n")
    )
    respx.get(BASE).mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/html"}, text=_page("T", "Body")
        )
    )
    with pytest.raises(WebsiteUnreadable, match="robots"):
        await read_website(BASE)


@respx.mock
async def test_non_html_is_rejected() -> None:
    respx.get(f"{BASE}/robots.txt").mock(return_value=httpx.Response(404))
    respx.get(BASE).mock(
        return_value=httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=b"%PDF"
        )
    )
    with pytest.raises(WebsiteUnreadable, match="not HTML"):
        await read_website(BASE)


@respx.mock
async def test_follows_one_redirect() -> None:
    respx.get(f"{BASE}/robots.txt").mock(return_value=httpx.Response(404))
    respx.get(url__eq=BASE).mock(
        return_value=httpx.Response(301, headers={"location": f"{BASE}/home"})
    )
    respx.get(url__eq=f"{BASE}/home").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/html"}, text=_page("Home", "Welcome")
        )
    )
    site = await read_website(BASE)
    assert site.pages == [f"{BASE}/home"]
    assert "Welcome" in site.text


@respx.mock
async def test_redirect_to_private_host_is_blocked() -> None:
    respx.get(f"{BASE}/robots.txt").mock(return_value=httpx.Response(404))
    respx.get(url__eq=BASE).mock(
        return_value=httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
    )
    with pytest.raises(UrlNotAllowed):
        await read_website(BASE)


async def test_private_and_non_http_hosts_are_blocked() -> None:
    for url in ("http://127.0.0.1/", "http://localhost/", "ftp://example.com/", "http://10.0.0.5/"):
        with pytest.raises(UrlNotAllowed):
            await read_website(url)


@respx.mock
async def test_text_is_capped_at_12000_chars() -> None:
    respx.get(f"{BASE}/robots.txt").mock(return_value=httpx.Response(404))
    long_body = "word " * 6000
    respx.get(BASE).mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/html"}, text=_page("Long", long_body)
        )
    )
    site = await read_website(BASE)
    assert site.chars == MAX_TEXT_CHARS
