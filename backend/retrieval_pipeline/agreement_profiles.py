"""Agreement type and user-role profiles for contract risk analysis."""

from typing import Dict, List, Tuple


AGREEMENT_USER_TYPE_MAP: Dict[str, List[str]] = {
    "Company Sales Agreement": ["Buyer", "Seller"],
    "Merger Agreement": ["Acquirer", "Target Company", "Shareholder"],
    "Stakeholder Agreement": ["Majority Shareholder", "Minority Shareholder", "Company Board"],
    "Rent Agreement": ["Landlord", "Tenant"],
}


ROLE_REVIEW_GUIDANCE: Dict[str, Dict[str, str]] = {
    "Company Sales Agreement": {
        "Buyer": (
            "Prioritize hidden liabilities, weak seller warranties, broad liability caps, "
            "insufficient indemnities, and unfavorable post-closing obligations for the buyer."
        ),
        "Seller": (
            "Prioritize over-broad indemnity duties, delayed or conditional payment terms, "
            "excessive escrow/holdback terms, and restrictive post-sale covenants on the seller."
        ),
    },
    "Merger Agreement": {
        "Acquirer": (
            "Prioritize unknown liabilities, weak closing conditions, integration obligations, "
            "and termination/break-fee structures that increase acquirer risk."
        ),
        "Target Company": (
            "Prioritize valuation uncertainty, one-sided representations, restrictive interim covenants, "
            "and deal-certainty terms that disadvantage the target."
        ),
        "Shareholder": (
            "Prioritize dilution impact, voting and consent rights, payout mechanics, "
            "and post-merger governance protections for shareholders."
        ),
    },
    "Stakeholder Agreement": {
        "Majority Shareholder": (
            "Prioritize deadlock rules, transfer restrictions, governance controls, "
            "and obligations that could materially limit majority control."
        ),
        "Minority Shareholder": (
            "Prioritize minority protections, information rights, anti-dilution protections, "
            "tag-along rights, and unfair exit restrictions."
        ),
        "Company Board": (
            "Prioritize governance clarity, fiduciary exposure, conflict-management terms, "
            "and enforceability of board decision workflows."
        ),
    },
    "Rent Agreement": {
        "Landlord": (
            "Prioritize payment default remedies, maintenance obligations, damage recovery, "
            "and tenant termination/assignment clauses from the landlord perspective."
        ),
        "Tenant": (
            "Prioritize rent escalation, repair burdens, deposit forfeiture triggers, "
            "early termination penalties, and unilateral landlord rights."
        ),
    },
}


DEFAULT_AGREEMENT_TYPE = "Company Sales Agreement"


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().split()).lower()


def get_agreement_type_user_type_map() -> Dict[str, List[str]]:
    """Return a copy of allowed agreement and user-type combinations."""
    return {agreement: list(user_types) for agreement, user_types in AGREEMENT_USER_TYPE_MAP.items()}


def get_allowed_agreement_types() -> List[str]:
    """Return all allowed agreement types."""
    return list(AGREEMENT_USER_TYPE_MAP.keys())


def get_allowed_user_types(agreement_type: str) -> List[str]:
    """Return allowed user types for a canonical agreement type."""
    return list(AGREEMENT_USER_TYPE_MAP.get(agreement_type, []))


def canonicalize_agreement_type(agreement_type: str) -> str:
    """Resolve agreement type to canonical value using case-insensitive matching."""
    target = _normalize(agreement_type)
    for allowed in AGREEMENT_USER_TYPE_MAP:
        if _normalize(allowed) == target:
            return allowed
    return ""


def canonicalize_user_type(agreement_type: str, user_type: str) -> str:
    """Resolve user type to canonical value for the given agreement type."""
    target = _normalize(user_type)
    for allowed in AGREEMENT_USER_TYPE_MAP.get(agreement_type, []):
        if _normalize(allowed) == target:
            return allowed
    return ""


def validate_agreement_selection(agreement_type: str, user_type: str) -> Tuple[str, str]:
    """Validate and return canonical (agreement_type, user_type)."""
    canonical_agreement = canonicalize_agreement_type(agreement_type)
    if not canonical_agreement:
        allowed = ", ".join(get_allowed_agreement_types())
        raise ValueError(f"Unsupported agreement_type '{agreement_type}'. Allowed values: {allowed}.")

    canonical_user = canonicalize_user_type(canonical_agreement, user_type)
    if not canonical_user:
        allowed_users = ", ".join(get_allowed_user_types(canonical_agreement))
        raise ValueError(
            f"Unsupported user_type '{user_type}' for agreement_type '{canonical_agreement}'. "
            f"Allowed values: {allowed_users}."
        )

    return canonical_agreement, canonical_user


def build_role_review_context(agreement_type: str, user_type: str) -> str:
    """Build a deterministic role-aware prompt segment."""
    guidance = ROLE_REVIEW_GUIDANCE.get(agreement_type, {}).get(
        user_type,
        "Prioritize legal, commercial, and compliance risk to this user role.",
    )
    return (
        f"Agreement type: {agreement_type}. "
        f"Review perspective: {user_type}. "
        f"Guidance: {guidance}"
    )
