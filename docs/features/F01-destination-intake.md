# F01. Destination intake

**Purpose:** turn a destination name (and optional website) into a confirmed list of 5–15 **signature items** that define what the place offers.

**User story:** As a DMO marketer, I type "Lisbon" and my tourism site, and within a minute I have an editable list of what makes Lisbon distinctive.

## How it works

1. Inputs: `destination_name` (required), `country` (required), `website_url` (optional).
2. If a URL is given: validate scheme (http/https); resolve the host and block private, loopback, link-local and metadata IPs on every redirect (SSRF guard); max 3 redirects, 1.5 MB per page, `text/html` only, robots.txt respected. Read the homepage plus up to 2 same-domain pages whose link text matches see/do/eat/culture/events. Extract text with trafilatura; cap at 12,000 characters total.
3. The agent calls the LLM (`destination_items.md`) for up to 15 **names** of signature items, each with a kind: `landmark`, `neighbourhood`, `dish`, `drink`, `venue`, `festival`, `music`, `film`, `book`, `brand`. Output validated with Pydantic. Website text is wrapped as untrusted data in the prompt.
4. Without a website, the LLM proposes items from the name and country only; the UI labels them "suggested from general knowledge, please check".
5. The user edits, removes and adds items, then confirms. Stored as `destinations` and `signature_items`. Website text kept 30 days for debugging, then deleted.

## Failure handling

| Failure | Behaviour |
|---|---|
| URL blocked | 422 `url_not_allowed` |
| Site unreadable | Continue from name only, with a notice |
| LLM unavailable or invalid twice | Empty editable list for manual entry |
| More than 15 items | First 15 kept; user can swap |

## UI

Wizard step 1 (name, country, website) and step 2 (editable item chips grouped by kind).

## Tests

SSRF cases (`127.0.0.1`, `10.x`, `169.254.169.254`, `[::1]`, redirect to private); page selection and text cap; LLM parse, repair, manual fallback with `FakeProvider`; API test of the full intake with respx-mocked site.

Acceptance: INT-01 to INT-05, SEC-02.
