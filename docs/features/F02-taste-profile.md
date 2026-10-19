# F02. Taste profile

**Purpose:** convert signature items into **Qloo entities and tags**, the destination's taste profile used by every later step.

## How it works

1. For each item, call Qloo `/search` with the item name plus the destination for places and localities ("Pastéis de Belém Lisbon"), and with the entity types mapped from the item kind (`landmark`/`venue`/`neighbourhood` → place or locality; `music` → artist; `film` → movie; `book` → book; `drink`/`brand` → brand; `dish` → place or tag search).
2. Accept the top result only if normalised name similarity ≥ 0.85 **and**, for places, its coordinates fall inside the destination's radius (from the destination entity or a geocode in Phase 0). Otherwise mark `unresolved`.
3. If the destination itself exists as a Qloo destination or locality entity, store it as `role = destination` (used by Strategy D).
4. Collect tags from resolved entities (and `/v2/tags` searches for dish or theme items if needed). Keep tags that appear on at least 2 entities or are directly searched; these form the **profile tags**.
5. Minimum to continue: at least 3 resolved entities. The user sees resolved and unresolved items and can remove entities or add via Qloo search.

## Storage

`profile_entities` (run_id, item_id, qloo_entity_id, name, type, role, similarity, source_call_id), `profile_tags` (run_id, tag_id, label, count).

## Failure handling

Unresolved items listed with reasons; fewer than 3 resolved → `profile_too_thin` and the run cannot start; Qloo errors → retry policy then fail closed (`qloo_unavailable`).

## UI

Profile step: entity chips with type icons, tag cloud with counts, unresolved list, "add from Qloo" search.

## Tests

Name matching thresholds; place radius check; tag aggregation rule; minimum-entities rule; type guard on silent failures; cache reuse; API test with fixtures.

Acceptance: PRF-01 to PRF-05.
