"""Entity resolution, typing, and relation extraction engine."""

import re
from typing import List, Dict, Any, Tuple

# Entity alias map for entity resolution
KNOWN_ENTITY_ALIASES = {
    "openai": ("OpenAI", "Company"),
    "openai inc": ("OpenAI", "Company"),
    "deepseek": ("DeepSeek", "Company"),
    "deepseek-ai": ("DeepSeek", "Company"),
    "google": ("Google", "Company"),
    "google quantum ai": ("Google Quantum AI", "Company"),
    "anthropic": ("Anthropic", "Company"),
    "meta": ("Meta", "Company"),
    "meta platforms": ("Meta", "Company"),
    "microsoft": ("Microsoft", "Company"),
    "apple": ("Apple", "Company"),
    "nvidia": ("NVIDIA", "Company"),
    "tesla": ("Tesla", "Company"),
    "toyota": ("Toyota", "Company"),
    "spacex": ("SpaceX", "Company"),
    "mit": ("MIT", "Company"),
    "cern": ("CERN", "Company"),
    "asml": ("ASML", "Company"),
    "moderna": ("Moderna", "Company"),
    "neuralink": ("Neuralink", "Company"),
    "waymo": ("Waymo", "Company"),
    "deepmind": ("DeepMind", "Company"),
    "replit": ("Replit", "Company"),
    "gnome": ("GNOME", "Company"),
}

# Key technologies
KNOWN_TECHNOLOGIES = {
    "solid-state battery": "Solid-State Battery",
    "solid state battery": "Solid-State Battery",
    "quantum computing": "Quantum Computing",
    "quantum circuits": "Quantum Circuits",
    "qubit memory": "Qubit Memory",
    "large language models": "Large Language Models",
    "llms": "Large Language Models",
    "ai agents": "AI Agents",
    "mixture-of-experts": "Mixture-of-Experts",
    "moe": "Mixture-of-Experts",
    "robotics": "Robotics",
    "robotic manipulation": "Robotic Manipulation",
    "mrna vaccine": "mRNA Vaccine",
    "alphafold": "AlphaFold",
    "microled": "MicroLED",
    "dna storage": "DNA Storage",
    "autonomous vehicles": "Autonomous Vehicles",
    "robotaxi": "Robotaxi",
    "lithography": "EUV Lithography",
    "crispr": "CRISPR",
    "macular degeneration implant": "Prima Visual Implant",
}

# Relation trigger patterns (regex -> relation_type)
RELATION_PATTERNS = [
    (r"(?:develops?|developed|developing|built|creates?|created|unveils?|unveiled|releases?|released|launches?|launched|presents?|presented)\s+(?:a\s+|an\s+|the\s+)?([A-Za-z0-9\- ]+)", "develops"),
    (r"(?:improves?|improved|improving|advances?|advanced|enhances?|enhanced|accelerates?)\s+(?:on\s+)?([A-Za-z0-9\- ]+)", "improves"),
    (r"(?:competes?\s+with|rivals?|challenges?)\s+([A-Za-z0-9\- ]+)", "competes_with"),
    (r"(?:partners?\s+with|collaborates?\s+with|teams?\s+up\s+with|working\s+with)\s+([A-Za-z0-9\- ]+)", "partners_with"),
    (r"(?:tested\s+in|deployed\s+in|demonstrated\s+in)\s+([A-Za-z0-9\- ]+)", "deployed_in"),
]


def resolve_entity(name: str) -> Tuple[str, str]:
    """
    Resolve and normalize entity name to canonical form and entity type.
    Returns (canonical_name, entity_type).
    """
    cleaned = name.strip()
    lower = cleaned.lower()

    # Check known companies / labs
    if lower in KNOWN_ENTITY_ALIASES:
        return KNOWN_ENTITY_ALIASES[lower]

    # Check known technologies
    for tech_key, canon_tech in KNOWN_TECHNOLOGIES.items():
        if tech_key in lower:
            return canon_tech, "Technology"

    # Default heuristic: Title Cased or Acronyms
    if cleaned.isupper() and len(cleaned) <= 6:
        return cleaned, "Technology"
    
    # Capitalized entity heuristic
    return cleaned.title(), "Entity"


def extract_entities_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Extract known and salient named entities from title and text.
    Returns list of unique (canonical_name, entity_type) pairs.
    """
    found = {}
    lower_text = text.lower()

    # 1. Match known companies / organizations
    for alias, (canon_name, e_type) in KNOWN_ENTITY_ALIASES.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, lower_text):
            found[canon_name] = e_type

    # 2. Match known technologies
    for tech_key, canon_name in KNOWN_TECHNOLOGIES.items():
        pattern = r"\b" + re.escape(tech_key) + r"\b"
        if re.search(pattern, lower_text):
            found[canon_name] = "Technology"

    # 3. Capitalized named phrases (e.g. proper nouns: "Blackwell Ultra", "AlphaFold 3", "LIBERO-PeRM")
    caps = re.findall(r"\b[A-Z][a-zA-Z0-9\-]*(?:\s+[A-Z][a-zA-Z0-9\-]*)+\b", text)
    for cap in caps:
        clean_cap = cap.strip()
        if len(clean_cap) > 3 and clean_cap.lower() not in ["the download", "new york", "united states", "sat sat", "all rights"]:
            if clean_cap not in found:
                found[clean_cap] = "Technology" if any(w in clean_cap.lower() for w in ["model", "system", "architecture", "algorithm", "network", "circuit", "implant", "chip"]) else "Entity"

    return list(found.items())


def extract_relations_from_text(
    text: str, source_id: int, published: str = ""
) -> List[Dict[str, Any]]:
    """
    Extract directed relation triples (subject, relation_type, object, confidence)
    connecting entities detected in the text.
    """
    entities = extract_entities_from_text(text)
    if len(entities) < 2:
        return []

    triples = []
    text_lower = text.lower()

    # Identify company / lab subjects
    subjects = [e for e in entities if e[1] == "Company"]
    objects = [e for e in entities if e[1] in ("Technology", "Entity")]

    # If no company found, link top technology entities
    if not subjects:
        subjects = [entities[0]]
        objects = entities[1:]

    for s_name, s_type in subjects:
        for o_name, o_type in objects:
            if s_name == o_name:
                continue

            # Determine relation type from sentence context
            rel_type = "mentions"
            confidence = 0.7

            for pattern, relation in RELATION_PATTERNS:
                # Look for subject followed by relation followed by object
                combined_pattern = rf"\b{re.escape(s_name.lower())}\b.*?" + pattern
                if re.search(combined_pattern, text_lower, re.DOTALL):
                    rel_type = relation
                    confidence = 0.92
                    break

            triples.append({
                "source_name": s_name,
                "source_type": s_type,
                "target_name": o_name,
                "target_type": o_type,
                "relation_type": rel_type,
                "confidence": confidence,
                "source_id": source_id,
                "occurred_at": published,
            })

    return triples
