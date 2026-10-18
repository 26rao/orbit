"""Structured JSON schemas and claim taxonomy for ORBIT reasoning."""

from typing import List, Dict, Any, Optional

ORBIT_REASONING_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Executive intelligence summary answering the query."
        },
        "verified_facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string"},
                    "source_id": {"type": "integer"},
                    "confidence": {"type": "number"}
                },
                "required": ["fact", "source_id"]
            },
            "description": "Directly supported facts with verifiable source citations."
        },
        "reported_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "source_id": {"type": "integer"},
                    "reported_by": {"type": "string"}
                },
                "required": ["claim", "source_id"]
            },
            "description": "Claims made by monitored entities or reports not yet independently replicated."
        },
        "emerging_signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signal": {"type": "string"},
                    "domain": {"type": "string"}
                },
                "required": ["signal"]
            },
            "description": "Early weak signals or experimental developments worth watching."
        },
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis": {"type": "string"},
                    "rationale": {"type": "string"}
                },
                "required": ["hypothesis", "rationale"]
            },
            "description": "Explicitly labeled AI-generated hypotheses and potential trajectories."
        },
        "uncertainty_assessment": {
            "type": "string",
            "description": "Explicit statement of data gaps, unknown factors, or conflicting reports."
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "url": {"type": "string"}
                },
                "required": ["source_id", "title", "url"]
            }
        }
    },
    "required": [
        "summary",
        "verified_facts",
        "reported_claims",
        "emerging_signals",
        "hypotheses",
        "uncertainty_assessment",
        "citations"
    ]
}
