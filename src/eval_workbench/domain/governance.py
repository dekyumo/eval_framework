"""Governance / NIST AI RMF profile attached to an agent snapshot.

Persisted on the `AgentSnapshot` exactly like `AgentDistribution` (no separate
store). See issues/rescan_persistence_two_scan_modes.md for the known re-scan
limitation this intentionally shares.
"""

from pydantic import BaseModel


class GovernanceProfile(BaseModel):
    """Human-curated NIST AI RMF profile for an agent snapshot."""

    concern_coverage: str = ""   # freeform: which tags cover which NIST concerns
    business_case: str = ""      # business justification (MAP-3 scope/costs)
