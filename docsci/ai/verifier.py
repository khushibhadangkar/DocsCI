"""Claim verification engine and human-accuracy draft emitter."""

from __future__ import annotations

import re
from datetime import date

from docsci.models import ClaimVerification, CommitEntry

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "with", "from", "by", "and",
    "or", "of", "is", "are", "was", "were", "be", "been", "has", "have", "had",
    "this", "that", "these", "those", "added", "capability", "resolved", "issue",
    "update", "key", "notable", "highlights", "updates", "features", "release",
}


def split_into_claims(summary_text: str) -> list[str]:
    """Extract individual atomic claims from AI summary text.

    Extracts bullet points and distinct sentences, skipping markdown headers.
    """
    claims: list[str] = []
    lines = summary_text.splitlines()

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Bullet point claim
        if line.startswith(("-", "*", "•")):
            clean = line.lstrip("-*• ").strip()
            if clean:
                claims.append(clean)
            continue

        # Prose sentence claims
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
        for s in sentences:
            if len(s.split()) >= 3:
                claims.append(s)

    return claims


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful content keywords for matching."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    words = {w for w in cleaned.split() if len(w) > 2 and w not in STOP_WORDS}
    return words


def verify_claims(
    claims: list[str],
    commits: list[CommitEntry],
) -> list[ClaimVerification]:
    """Verify each AI summary claim against commit evidence.

    Marks each claim as SUPPORTED (with commit hashes) or UNSUPPORTED.
    """
    verifications: list[ClaimVerification] = []

    # Pre-index commits with their keywords
    commit_indexes: list[tuple[CommitEntry, set[str]]] = []
    for c in commits:
        text = f"{c.type} {c.scope or ''} {c.description} {c.body}"
        kws = extract_keywords(text)
        commit_indexes.append((c, kws))

    for idx, claim in enumerate(claims, start=1):
        claim_kws = extract_keywords(claim)
        evidence_hashes: list[str] = []

        for commit, c_kws in commit_indexes:
            overlap = claim_kws.intersection(c_kws)
            # A commit provides evidence if it shares at least 2 key terms or significant scope overlap
            if len(overlap) >= 2 or (commit.scope and commit.scope.lower() in claim_kws and len(overlap) >= 1):
                evidence_hashes.append(commit.short_hash)

        if evidence_hashes:
            verifications.append(
                ClaimVerification(
                    claim_id=idx,
                    claim_text=claim,
                    status="SUPPORTED",
                    evidence_hashes=sorted(set(evidence_hashes)),
                    notes="Verified against commit messages",
                )
            )
        else:
            verifications.append(
                ClaimVerification(
                    claim_id=idx,
                    claim_text=claim,
                    status="UNSUPPORTED",
                    evidence_hashes=[],
                    notes="No corroborating commit found in release range. Potential hallucination.",
                )
            )

    return verifications


def generate_draft_markdown(
    summary_text: str,
    verifications: list[ClaimVerification],
    commits: list[CommitEntry],
    prompt_version: str = "v1.0.0",
    version_label: str = "v1.0.0",
) -> str:
    """Generate RELEASE_NOTES_DRAFT.md with required review banner and audit table."""
    today_str = date.today().isoformat()
    unsupported = [v for v in verifications if v.status == "UNSUPPORTED"]
    clean_version = version_label.lstrip("v")

    lines: list[str] = [
        "---",
        f"title: AI-Assisted Draft Release Notes for {clean_version}",
        f"description: Draft release summary with claim verification audit for {clean_version}",
        f"product_version: '{clean_version}'",
        f"last_reviewed: '{today_str}'",
        "owner: docs-team",
        "---",
        "",
        "> [!WARNING]",
        "> **AI-assisted draft: requires human review.**",
        "> Every AI-generated summary must pass human technical verification before publication.",
        "> Never publish this draft automatically.",
        "",
        f"# Draft release notes for version {clean_version}",
        "",
        f"**Metadata:** Generated on `{today_str}` | Prompt version: `{prompt_version}` | "
        f"Target version: `{version_label}`",
        "",
    ]

    if unsupported:
        lines.append("> [!CAUTION]")
        lines.append(f"> **UNSUPPORTED CLAIMS DETECTED ({len(unsupported)} claim(s))**:")
        lines.append(
            "> The following statements could not be verified against commit evidence "
            "and require manual human verification or removal before publication:"
        )
        for u in unsupported:
            lines.append(f"> - **Claim {u.claim_id}:** {u.claim_text}")
        lines.append("")

    lines.append("## AI-generated summary")
    lines.append("")
    lines.append(summary_text.strip())
    lines.append("")

    lines.append("## Claim verification audit")
    lines.append("")
    lines.append("| ID | Status | Claim Statement | Evidence Commits | Reviewer Notes |")
    lines.append("|---|---|---|---|---|")

    for v in verifications:
        status_badge = "✅ SUPPORTED" if v.status == "SUPPORTED" else "⚠️ UNSUPPORTED"
        ev_str = ", ".join(f"`{h}`" for h in v.evidence_hashes) if v.evidence_hashes else "None"
        # Escape pipe characters in claims
        safe_claim = v.claim_text.replace("|", "/")
        lines.append(f"| {v.claim_id} | {status_badge} | {safe_claim} | {ev_str} | {v.notes} |")

    lines.append("")
    lines.append("## Underlying commit history")
    lines.append("")
    for c in commits:
        lines.append(c.display_line())
    lines.append("")

    return "\n".join(lines)
