"""Enrich the registry with reviewed official organization evidence.

This module intentionally keeps the evidence table explicit.  It does not crawl,
log in, or infer affiliations from email domains.  Exact, unique public-name
matches may be materialized; every other match remains in a review CSV.
"""

from __future__ import annotations

import csv
import json
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .ids import stable_id


DEFAULT_RUN = Path("consulting/runs/vtuber_registry_20260805")


OFFICIAL_SOURCES = [
    {
        "uri": "https://stellive.me/about",
        "publisher": "StelLive",
        "supports": ["affiliation"],
        "note": "Official company page describing StelLive as a VTuber company.",
    },
    {
        "uri": "https://stellive.me/news",
        "publisher": "StelLive",
        "supports": ["affiliation", "name", "activity"],
        "note": "Official news index used for current talent-name and activity evidence.",
    },
    {
        "uri": "https://www.meechu.com/?mode=privacy",
        "publisher": "meechu / SCON",
        "supports": ["affiliation", "name"],
        "note": "Official meechu page listing its virtual creators.",
    },
    {
        "uri": "https://www.meechu.com/guide",
        "publisher": "meechu / SCON",
        "supports": ["affiliation"],
        "note": "Official guideline identifying SCON as operator of meechu.",
    },
    {
        "uri": "https://www.akaiv.studio/",
        "publisher": "AKAIV STUDIO",
        "supports": ["affiliation", "name", "account_link"],
        "note": "Official studio page listing members and their SOOP links.",
    },
    {
        "uri": "https://www.enchantenter.co.kr/creator",
        "publisher": "Enchant Entertainment",
        "supports": ["affiliation", "name", "account_link"],
        "note": "Official creator directory; only entries explicitly described as virtual are used here.",
    },
    {
        "uri": "https://gysent.com/creators",
        "publisher": "CHARON CREATIVE",
        "supports": ["affiliation", "name"],
        "note": "Official CHARON creator directory and organization evidence.",
    },
    {
        "uri": "https://gysent.com/partners/?bmode=view&idx=168469360",
        "publisher": "CHARON CREATIVE",
        "supports": ["affiliation", "name"],
        "note": "Official partner case identifying Arisa as CHARON UNIVERSE AESTHER.",
    },
    {
        "uri": "https://gysent.com/partners/?bmode=view&idx=168470539",
        "publisher": "CHARON CREATIVE",
        "supports": ["affiliation", "name"],
        "note": "Official partner case identifying Eris as CHARON UNIVERSE AESTHER.",
    },
    {
        "uri": "https://pixelstore.kr/",
        "publisher": "PIXEL NETWORK",
        "supports": ["affiliation", "name"],
        "note": "Official company-operated store; confirms the corporation and separates PIXEL from external creators.",
    },
    {
        "uri": "https://virtualunion.net/",
        "publisher": "VIRTUAL UNION",
        "supports": ["affiliation", "name"],
        "note": "Official association page identifying Virtual Union and its four member companies.",
    },
    {
        "uri": "https://www.sandbox.co.kr/",
        "publisher": "SANDBOX NETWORK",
        "supports": ["affiliation", "name"],
        "note": "Official company and creator-business page.",
    },
    {
        "uri": "https://sandbox.co.kr/news_list",
        "publisher": "SANDBOX NETWORK",
        "supports": ["affiliation", "name", "activity"],
        "note": "Official press page identifying current VEILIGHT and UR:L members and platforms.",
    },
    {
        "uri": "https://www.youtube.com/watch?v=Li4VvoZGiYs",
        "publisher": "WAKTAVERSE",
        "supports": ["affiliation", "name", "account_link", "vtuber_identity"],
        "note": "Verified official WAKTAVERSE channel description identifying ISEGYE IDOL and its six members.",
    },
    {
        "uri": "https://x.com/projecti_kr",
        "publisher": "PROJECT i",
        "supports": ["affiliation", "name"],
        "note": "Official PROJECT i account metadata observed through the public search index; X page is JS-only.",
    },
    {
        "uri": "https://music.bugs.co.kr/artist/80398251",
        "publisher": "Bugs",
        "source_tier": "P1",
        "supports": ["affiliation", "name"],
        "note": "Public music-platform artist page listing the six HONEYZ members.",
    },
    {
        "uri": "https://x.com/listella_on",
        "publisher": "LISTELLA",
        "supports": ["affiliation", "name", "activity"],
        "note": "Official LISTELLA account metadata and current activity observed through the public search index.",
    },
]


ORGANIZATION_UPDATES = {
    "스텔라이브": {
        "display_name": "스텔라이브",
        "aliases": ["StelLive"],
        "organization_type": "agency",
        "domains": ["stellive.me"],
        "source_uris": ["https://stellive.me/about", "https://stellive.me/news"],
    },
    "미츄": {
        "display_name": "미츄",
        "aliases": ["meechu"],
        "organization_type": "project",
        "domains": ["meechu.com"],
        "source_uris": [
            "https://www.meechu.com/?mode=privacy",
            "https://www.meechu.com/guide",
        ],
    },
    "아카이브": {
        "display_name": "AKAIV STUDIO",
        "aliases": ["아카이브", "AkaiV"],
        "organization_type": "agency",
        "domains": ["akaiv.studio"],
        "source_uris": ["https://www.akaiv.studio/"],
    },
    "인챈트": {
        "display_name": "인챈트 엔터테인먼트",
        "aliases": ["인챈트", "Enchant"],
        "organization_type": "agency",
        "domains": ["enchantenter.co.kr"],
        "source_uris": ["https://www.enchantenter.co.kr/creator"],
    },
    "지와이에스": {
        "display_name": "카론 크리에이티브",
        "aliases": ["지와이에스", "GYS", "CHARON CREATIVE"],
        "organization_type": "agency",
        "domains": ["gysent.com"],
        "source_uris": ["https://gysent.com/creators"],
    },
    "에스더": {
        "display_name": "에스더",
        "aliases": ["AESTHER", "CHARON UNIVERSE AESTHER"],
        "organization_type": "project",
        "domains": ["gysent.com"],
        "source_uris": [
            "https://gysent.com/partners/?bmode=view&idx=168469360",
            "https://gysent.com/partners/?bmode=view&idx=168470539",
        ],
    },
    "픽셀네트워크": {
        "display_name": "픽셀네트워크",
        "aliases": ["PIXEL NETWORK", "픽셀컴퍼니"],
        "organization_type": "corporation",
        "domains": ["pixelnetwork.co.kr", "pixelstore.kr"],
        "source_uris": ["https://pixelstore.kr/"],
    },
    "버츄얼 유니온": {
        "display_name": "버츄얼 유니온",
        "aliases": ["VIRTUAL UNION"],
        "organization_type": "collective",
        "domains": ["virtualunion.net"],
        "source_uris": ["https://virtualunion.net/"],
    },
    "샌드박스네트워크": {
        "display_name": "샌드박스네트워크",
        "aliases": ["SANDBOX NETWORK"],
        "organization_type": "corporation",
        "domains": ["sandbox.co.kr", "sandboxnetwork.net"],
        "source_uris": ["https://www.sandbox.co.kr/", "https://sandbox.co.kr/news_list"],
    },
    "이세계아이돌": {
        "display_name": "이세계아이돌",
        "aliases": ["ISEGYE IDOL", "이세돌"],
        "organization_type": "collective",
        "domains": [],
        "source_uris": ["https://www.youtube.com/watch?v=Li4VvoZGiYs"],
    },
    "허니즈": {
        "display_name": "허니즈",
        "aliases": ["HONEYZ", "PROJECT i HONEYZ"],
        "organization_type": "project",
        "domains": [],
        "source_uris": [
            "https://x.com/projecti_kr",
            "https://music.bugs.co.kr/artist/80398251",
        ],
    },
    "리스텔라": {
        "display_name": "리스텔라",
        "aliases": ["LISTELLA"],
        "organization_type": "agency",
        "domains": ["listella.tv"],
        "source_uris": ["https://x.com/listella_on"],
    },
}


DISCOVERED_ORGANIZATIONS = [
    {
        "seed_name": "TSURAI COMPANY",
        "aliases": ["츠라이 컴퍼니"],
        "organization_type": "corporation",
        "domains": [],
    },
    {
        "seed_name": "V-LLAGE",
        "aliases": ["브이리지", "DEVMATE V-LLAGE"],
        "organization_type": "project",
        "domains": [],
    },
    {
        "seed_name": "V-LUP",
        "aliases": ["브이럽", "CREATORBUS V-LUP"],
        "organization_type": "project",
        "domains": ["creatorbus.net"],
    },
    {
        "seed_name": "VIRTUAL HERTZ",
        "aliases": ["버츄얼 헤르츠", "VIRTUAL HERTZ ENT."],
        "organization_type": "agency",
        "domains": [],
    },
]


ROSTERS = [
    {
        "organization_seed": "스텔라이브",
        "source_uri": "https://stellive.me/news",
        "names": [
            "아야츠노 유니",
            "시라유키 히나",
            "네네코 마시로",
            "아카네 리제",
            "아라하시 타비",
            "텐코 시부키",
            "아오쿠모 린",
            "하나코 나나",
            "유즈하 리코",
            "사키하네 후야",
        ],
        "relationship": "talent",
    },
    {
        "organization_seed": "미츄",
        "source_uri": "https://www.meechu.com/?mode=privacy",
        "names": [
            "이오몽",
            "마젯",
            "미녕이데려오깨",
            "앵보",
            "세노",
            "부쿠키",
            "위도",
            "모아",
            "하지유",
            "희지",
        ],
        "relationship": "member",
    },
    {
        "organization_seed": "인챈트",
        "source_uri": "https://www.enchantenter.co.kr/creator",
        "names": ["둥그레", "티뭉"],
        "relationship": "managed",
    },
    {
        "organization_seed": "에스더",
        "source_uri_by_name": {
            "아리사": "https://gysent.com/partners/?bmode=view&idx=168469360",
            "에리스": "https://gysent.com/partners/?bmode=view&idx=168470539",
        },
        "names": ["아리사", "에리스"],
        "relationship": "member",
    },
    {
        "organization_seed": "샌드박스네트워크",
        "source_uri": "https://sandbox.co.kr/news_list",
        "names": [
            "RED레드",
            "시아 이르엘린",
            "루루엘 아스트리온",
            "모카",
            "랑코",
            "마냥",
            "솜먕",
        ],
        "relationship": "talent",
    },
    {
        "organization_seed": "이세계아이돌",
        "source_uri": "https://www.youtube.com/watch?v=Li4VvoZGiYs",
        "names": ["아이네", "징버거", "릴파", "주르르", "고세구", "비챤"],
        "relationship": "member",
    },
    {
        "organization_seed": "허니즈",
        "source_uri": "https://music.bugs.co.kr/artist/80398251",
        "names": ["허니츄러스", "아야", "담유이", "디디디용", "오화요", "망내"],
        "relationship": "member",
    },
]


AKAIV_OFFICIAL_ACCOUNTS = [
    ("우사미", "u3ams2", "https://ch.sooplive.co.kr/u3ams2"),
    ("여르미", "yeorumi030", "https://ch.sooplive.co.kr/yeorumi030"),
    ("한결", "kaksjak0730", "https://ch.sooplive.co.kr/kaksjak0730"),
    ("비몽", "beemong", "https://ch.sooplive.co.kr/beemong"),
    ("샤르망", "owozzz", "https://ch.sooplive.co.kr/owozzz"),
]


ISEGYE_OFFICIAL_ACCOUNTS = [
    ("아이네", "inehine", "https://ch.sooplive.co.kr/inehine"),
    ("징버거", "jingburger1", "https://ch.sooplive.co.kr/jingburger1"),
    ("릴파", "lilpa0309", "https://ch.sooplive.co.kr/lilpa0309"),
    ("주르르", "cotton1217", "https://ch.sooplive.co.kr/cotton1217"),
    ("고세구", "gosegu2", "https://ch.sooplive.co.kr/gosegu2"),
    ("비챤", "viichan6", "https://ch.sooplive.co.kr/viichan6"),
]


for _member_name, _soop_id, _soop_url in ISEGYE_OFFICIAL_ACCOUNTS:
    OFFICIAL_SOURCES.append(
        {
            "uri": _soop_url,
            "publisher": "SOOP",
            "source_tier": "P1",
            "supports": ["account_link", "activity"],
            "note": f"Public SOOP station candidate for ISEGYE IDOL member {_member_name}.",
        }
    )


def run_enrichment(run_dir: str | Path = DEFAULT_RUN) -> dict[str, int]:
    run = Path(run_dir)
    normalized = run / "20_normalized"
    review_dir = run / "40_review"
    coverage = run / "50_coverage"
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    sources_path = normalized / "sources.ndjson"
    organizations_path = normalized / "organizations.ndjson"
    accounts_path = normalized / "accounts.ndjson"
    affiliations_path = normalized / "affiliations.ndjson"
    reviews_path = review_dir / "review_queue.ndjson"

    sources = list(_iter_ndjson(sources_path))
    source_by_uri = {record["uri"]: record for record in sources}
    for item in OFFICIAL_SOURCES:
        source_by_uri[item["uri"]] = {
            "record_type": "source",
            "source_id": stable_id("source", item["uri"]),
            "uri": item["uri"],
            "source_tier": item.get("source_tier", "P0"),
            "publisher": item["publisher"],
            "observed_at": now,
            "supports": item["supports"],
            "note": item["note"],
            "secret_values_stored": False,
        }
    sources = sorted(source_by_uri.values(), key=lambda item: item["source_id"])

    organizations = list(_iter_ndjson(organizations_path))
    original_seed_names = {
        record["organization_id"]: _find_seed_name(record)
        for record in organizations
    }
    organization_by_seed = {
        seed: record
        for seed in ORGANIZATION_UPDATES
        for record in organizations
        if seed == record["display_name"] or seed in record.get("aliases", [])
    }
    for seed, update in ORGANIZATION_UPDATES.items():
        record = organization_by_seed.get(seed)
        if record is None:
            raise KeyError(f"organization seed not found: {seed}")
        record.update(
            display_name=update["display_name"],
            aliases=sorted(set(record.get("aliases", [])) | set(update["aliases"])),
            organization_type=update["organization_type"],
            domains=sorted(set(record.get("domains", [])) | set(update["domains"])),
            review_status="manual_confirmed",
            source_ids=sorted(
                set(record.get("source_ids", []))
                | {source_by_uri[uri]["source_id"] for uri in update["source_uris"]}
            ),
        )
    union_source_id = source_by_uri["https://virtualunion.net/"]["source_id"]
    existing_org_ids = {record["organization_id"] for record in organizations}
    for item in DISCOVERED_ORGANIZATIONS:
        organization_id = stable_id("organization", _normalized_name(item["seed_name"]))
        if organization_id in existing_org_ids:
            continue
        record = {
            "record_type": "organization",
            "organization_id": organization_id,
            "display_name": item["seed_name"],
            "aliases": item["aliases"],
            "organization_type": item["organization_type"],
            "domains": item["domains"],
            "review_status": "manual_confirmed",
            "source_ids": [union_source_id],
        }
        organizations.append(record)
        existing_org_ids.add(organization_id)
        original_seed_names[organization_id] = item["seed_name"]
    organization_by_seed = {
        original_seed_names[record["organization_id"]]: record for record in organizations
    }

    accounts = list(_iter_ndjson(accounts_path))
    exact_accounts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for account in accounts:
        exact_accounts[account["display_name"]].append(account)

    affiliations = {record["affiliation_id"]: record for record in _iter_ndjson(affiliations_path)}
    reviews = {record["review_id"]: record for record in _iter_ndjson(reviews_path)}
    verified_organization_ids = {
        record["organization_id"]
        for record in organizations
        if record["review_status"] == "manual_confirmed"
    }
    organization_by_domain = {
        domain: record for record in organizations for domain in record.get("domains", [])
    }
    for review in reviews.values():
        if (
            review["issue_code"] == "organization_seed_requires_official_source"
            and review["entity_id"] in verified_organization_ids
        ):
            review["status"] = "resolved"
            organization = next(
                item for item in organizations if item["organization_id"] == review["entity_id"]
            )
            review["source_ids"] = sorted(
                set(review.get("source_ids", [])) | set(organization["source_ids"])
            )
        if review["issue_code"] == "agency_domain_requires_organization_mapping":
            domain = review.get("details", {}).get("domain")
            if domain in organization_by_domain:
                review["status"] = "resolved"
                review["source_ids"] = sorted(
                    set(review.get("source_ids", []))
                    | set(organization_by_domain[domain]["source_ids"])
                )
    roster_rows: list[dict[str, Any]] = []
    confirmed = 0
    review_candidates = 0

    for roster in ROSTERS:
        org = organization_by_seed[roster["organization_seed"]]
        for official_name in roster["names"]:
            source_uri = roster.get("source_uri") or roster["source_uri_by_name"][official_name]
            source = source_by_uri[source_uri]
            matching_accounts = exact_accounts.get(official_name, [])
            matching_personas = sorted({item["persona_id"] for item in matching_accounts})
            status = "needs_review"
            affiliation_id = ""
            if len(matching_personas) == 1:
                persona_id = matching_personas[0]
                affiliation_id = stable_id(
                    "affiliation",
                    persona_id,
                    org["organization_id"],
                    roster["relationship"],
                    "current",
                )
                affiliations[affiliation_id] = {
                    "record_type": "affiliation",
                    "affiliation_id": affiliation_id,
                    "persona_id": persona_id,
                    "organization_id": org["organization_id"],
                    "relationship": roster["relationship"],
                    "start_at": None,
                    "end_at": None,
                    "status": "current",
                    "source_ids": sorted(
                        {source["source_id"]}
                        | {
                            source_id
                            for account in matching_accounts
                            for source_id in account.get("source_ids", [])
                        }
                    ),
                }
                status = "materialized_exact_unique_name"
                confirmed += 1
            else:
                review_candidates += 1
                candidate_accounts = _substring_candidates(accounts, official_name)
                review_id = stable_id(
                    "review",
                    "official_roster_name_not_exact_unique",
                    org["organization_id"],
                    official_name,
                )
                reviews[review_id] = {
                    "record_type": "review_item",
                    "review_id": review_id,
                    "entity_type": "organization",
                    "entity_id": org["organization_id"],
                    "issue_code": "official_roster_name_not_exact_unique",
                    "severity": "warning",
                    "status": "open",
                    "details": {
                        "official_name": official_name,
                        "exact_account_count": len(matching_accounts),
                        "substring_candidate_account_ids": [
                            item["account_id"] for item in candidate_accounts
                        ],
                    },
                    "source_ids": [source["source_id"]],
                }
            roster_rows.append(
                {
                    "organization_seed": roster["organization_seed"],
                    "organization_id": org["organization_id"],
                    "official_name": official_name,
                    "source_uri": source_uri,
                    "exact_account_count": len(matching_accounts),
                    "matched_account_ids": "|".join(
                        account["account_id"] for account in matching_accounts
                    ),
                    "matched_persona_ids": "|".join(matching_personas),
                    "affiliation_id": affiliation_id,
                    "status": status,
                }
            )

    official_account_rows: list[dict[str, Any]] = []
    akaiv = organization_by_seed["아카이브"]
    akaiv_source = source_by_uri["https://www.akaiv.studio/"]
    natural_accounts = {(account["platform"], account["platform_account_id"]): account for account in accounts}
    for official_name, official_id, official_url in AKAIV_OFFICIAL_ACCOUNTS:
        direct = natural_accounts.get(("soop", official_id))
        candidates = _substring_candidates(accounts, official_name)
        official_account_rows.append(
            {
                "organization_seed": "아카이브",
                "organization_id": akaiv["organization_id"],
                "official_name": official_name,
                "platform": "soop",
                "official_platform_account_id": official_id,
                "official_url": official_url,
                "already_in_registry_account_id": direct["account_id"] if direct else "",
                "local_name_candidate_account_ids": "|".join(
                    item["account_id"] for item in candidates
                ),
                "status": "already_present" if direct else "needs_account_and_identity_review",
                "source_uri": akaiv_source["uri"],
                "note": "Softcon cid is not assumed to equal this official SOOP handle.",
            }
        )
        if direct is None:
            review_candidates += 1
            review_id = stable_id(
                "review", "official_soop_handle_missing_from_softcon_seed", akaiv["organization_id"], official_id
            )
            reviews[review_id] = {
                "record_type": "review_item",
                "review_id": review_id,
                "entity_type": "organization",
                "entity_id": akaiv["organization_id"],
                "issue_code": "official_soop_handle_missing_from_softcon_seed",
                "severity": "warning",
                "status": "open",
                "details": {
                    "official_name": official_name,
                    "official_platform_account_id": official_id,
                    "official_url": official_url,
                    "local_name_candidate_account_ids": [item["account_id"] for item in candidates],
                },
                "source_ids": [akaiv_source["source_id"]],
            }

    isegye = organization_by_seed["이세계아이돌"]
    isegye_source = source_by_uri["https://www.youtube.com/watch?v=Li4VvoZGiYs"]
    for official_name, official_id, official_url in ISEGYE_OFFICIAL_ACCOUNTS:
        direct = natural_accounts.get(("soop", official_id))
        candidates = _substring_candidates(accounts, official_name)
        platform_source = source_by_uri[official_url]
        official_account_rows.append(
            {
                "organization_seed": "이세계아이돌",
                "organization_id": isegye["organization_id"],
                "official_name": official_name,
                "platform": "soop",
                "official_platform_account_id": official_id,
                "official_url": official_url,
                "already_in_registry_account_id": direct["account_id"] if direct else "",
                "local_name_candidate_account_ids": "|".join(
                    item["account_id"] for item in candidates
                ),
                "status": "already_present" if direct else "missing_from_softcon_seed",
                "source_uri": official_url,
                "note": "Current official SOOP handle; absent handles expose a Softcon coverage gap.",
            }
        )
        if direct is None:
            review_candidates += 1
            review_id = stable_id(
                "review",
                "official_soop_handle_missing_from_softcon_seed",
                isegye["organization_id"],
                official_id,
            )
            reviews[review_id] = {
                "record_type": "review_item",
                "review_id": review_id,
                "entity_type": "organization",
                "entity_id": isegye["organization_id"],
                "issue_code": "official_soop_handle_missing_from_softcon_seed",
                "severity": "blocking",
                "status": "open",
                "details": {
                    "official_name": official_name,
                    "official_platform_account_id": official_id,
                    "official_url": official_url,
                    "local_name_candidate_account_ids": [item["account_id"] for item in candidates],
                },
                "source_ids": sorted([isegye_source["source_id"], platform_source["source_id"]]),
            }

    _write_ndjson(sources_path, sources)
    _write_ndjson(organizations_path, sorted(organizations, key=lambda item: item["organization_id"]))
    _write_ndjson(affiliations_path, sorted(affiliations.values(), key=lambda item: item["affiliation_id"]))
    _write_ndjson(reviews_path, sorted(reviews.values(), key=lambda item: item["review_id"]))

    _write_csv(review_dir / "official_roster_matches.csv", roster_rows)
    _write_csv(review_dir / "official_account_candidates.csv", official_account_rows)
    _write_organization_map(
        review_dir / "organization_source_map.csv", organizations, original_seed_names, source_by_uri
    )

    summary = {
        "official_sources": len(OFFICIAL_SOURCES),
        "organizations_confirmed": len(ORGANIZATION_UPDATES) + len(DISCOVERED_ORGANIZATIONS),
        "affiliations_materialized": confirmed,
        "new_review_candidates": review_candidates,
        "official_account_candidates": len(official_account_rows),
        "total_affiliations": len(affiliations),
        "total_reviews": len(reviews),
    }
    coverage.mkdir(parents=True, exist_ok=True)
    (coverage / "organization_enrichment_summary.json").write_text(
        json.dumps({"generated_at": now, **summary}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def _substring_candidates(accounts: list[dict[str, Any]], official_name: str) -> list[dict[str, Any]]:
    normalized_official = _normalized_name(official_name)
    if not normalized_official:
        return []

    candidates = []
    for account in accounts:
        normalized_account = _normalized_name(account.get("display_name") or "")
        if not normalized_account:
            continue
        if (
            normalized_official in normalized_account
            or normalized_account in normalized_official
        ):
            candidates.append(account)
    return candidates


def _find_seed_name(record: dict[str, Any]) -> str:
    candidates = [record["display_name"], *record.get("aliases", [])]
    for seed in ORGANIZATION_UPDATES:
        if seed in candidates:
            return seed
    return record["display_name"]


def _normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in normalized if char.isalnum())


def _write_organization_map(
    path: Path,
    organizations: list[dict[str, Any]],
    original_seed_names: dict[str, str],
    source_by_uri: dict[str, dict[str, Any]],
) -> None:
    rows = []
    for record in sorted(organizations, key=lambda item: original_seed_names[item["organization_id"]]):
        seed = original_seed_names[record["organization_id"]]
        update = ORGANIZATION_UPDATES.get(seed)
        rows.append(
            {
                "seed_name": seed,
                "canonical_name": record["display_name"],
                "organization_id": record["organization_id"],
                "organization_type": record["organization_type"],
                "domains": "|".join(record["domains"]),
                "verification_status": record["review_status"],
                "official_source_uris": "|".join(update["source_uris"]) if update else "",
                "source_ids": "|".join(record["source_ids"]),
                "note": "official evidence reviewed" if update else "seed remains unresolved",
            }
        )
    _write_csv(path, rows)


def _iter_ndjson(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _write_ndjson(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    print(run_enrichment())
