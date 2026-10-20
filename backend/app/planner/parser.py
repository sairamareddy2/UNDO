import re
from typing import Any, Dict, List, Tuple
from app.integrations.gemini_adapter import gemini_adapter


class ActionIntentParser:
    """
    Simulated Alexa+ Action Plan Generator.
    Parses natural language requests into structured action proposals.
    Uses Google Gemini (google-genai SDK) when GEMINI_API_KEY is present,
    with deterministic intent-based fallback.
    """

    @classmethod
    def parse_prompt(cls, prompt: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Parses a prompt into a list of tuples: (action_type, title, parameters)
        """
        text = prompt.strip()
        if not text:
            return []

        # 1. Attempt Gemini-driven structured parsing if configured
        if gemini_adapter.is_available():
            proposals = gemini_adapter.generate_action_proposals(text)
            if proposals:
                return proposals

        # 2. Deterministic rule-based intent parsing (Fallback & Baseline)
        return cls._parse_deterministic(text)

    @classmethod
    def _parse_deterministic(cls, text: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        lower = text.lower()
        actions: List[Tuple[str, str, Dict[str, Any]]] = []

        # 1. Dangerous / Disallowed intents check
        if any(w in lower for w in ["wipe database", "drop table", "format drive", "truncate database"]):
            actions.append((
                "wipe_database",
                "Wipe application database",
                {"target": "all_tables", "raw_prompt": text}
            ))
            return actions

        if any(w in lower for w in ["transfer funds", "send money", "wire cash", "purchase gift card"]):
            actions.append((
                "transfer_funds",
                "Unauthorized financial transaction",
                {"amount": 500, "currency": "USD", "raw_prompt": text}
            ))
            return actions

        if "delete account" in lower or "delete my account" in lower:
            actions.append((
                "delete_account",
                "Delete primary user account",
                {"confirmation": False, "raw_prompt": text}
            ))
            return actions

        # Check for multi-clause requests
        clauses = cls._split_intent_clauses(text)

        for clause in clauses:
            sub = clause.strip()
            if not sub:
                continue
            parsed = cls._parse_single_clause(sub)
            if parsed:
                actions.append(parsed)

        if not actions:
            actions.append((
                "unknown_request",
                f"Unrecognized request: '{text}'",
                {"raw_prompt": text}
            ))

        return actions

    @classmethod
    def _split_intent_clauses(cls, text: str) -> List[str]:
        parts = re.split(r'\. |\band then\b|\balso\b', text, flags=re.IGNORECASE)
        final_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            sub_splits = re.split(r'\s+and\s+(?=(?:add|buy|get|lock|unlock|remind|set|close|open)\b)', part, flags=re.IGNORECASE)
            final_parts.extend(sub_splits)
        return final_parts

    @classmethod
    def _parse_single_clause(cls, clause: str) -> Tuple[str, str, Dict[str, Any]]:
        lower = clause.lower()

        # Door actions: lock / unlock
        if any(w in lower for w in ["door", "patio", "garage"]):
            door_id = "front_door"
            if "back" in lower or "patio" in lower:
                door_id = "back_door"
            elif "garage" in lower:
                door_id = "garage_entry"

            target_state = "locked"
            if "unlock" in lower or "open" in lower:
                target_state = "unlocked"

            action_name = "Lock" if target_state == "locked" else "Unlock"
            door_label = door_id.replace("_", " ").title()

            return (
                "set_door_lock",
                f"{action_name} {door_label}",
                {"door_id": door_id, "target_state": target_state}
            )

        # Reminder actions
        if "remind" in lower or "reminder" in lower:
            time_match = re.search(r'\b(?:at|for|by)\s+([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm|a\.m\.|p\.m\.)|[0-9]{1,2}\s*(?:am|pm))', clause, re.IGNORECASE)
            remind_at = time_match.group(1).strip() if time_match else "9:00 AM"

            title_text = clause
            title_text = re.sub(r'^(?:please\s+)?(?:set\s+(?:a\s+)?reminder\s+(?:to|for)?|remind\s+(?:me\s+)?(?:to|about)?)\s*', '', title_text, flags=re.IGNORECASE)
            title_text = re.sub(r'\b(?:at|for|by)\s+[0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm|a\.m\.|p\.m\.)\b', '', title_text, flags=re.IGNORECASE)
            title_text = title_text.strip(" ,.:-")

            if not title_text:
                title_text = "Scheduled Task Reminder"

            return (
                "create_reminder",
                f"Reminder: {title_text.capitalize()} at {remind_at}",
                {"title": title_text.capitalize(), "remind_at": remind_at, "priority": "medium"}
            )

        # Grocery actions: add / buy / purchase / get
        if any(w in lower for w in ["grocer", "buy", "cart", "milk", "eggs", "bread", "apples", "bananas", "coffee", "add"]):
            qty_match = re.search(r'\b(\d+)\b', clause)
            quantity = int(qty_match.group(1)) if qty_match else 1

            clean_item = clause
            clean_item = re.sub(r'^(?:please\s+)?(?:add\s+|buy\s+|get\s+|order\s+)', '', clean_item, flags=re.IGNORECASE)
            clean_item = re.sub(r'\b(?:to\s+(?:my\s+)?(?:grocery\s+list|cart|shopping\s+list))\b', '', clean_item, flags=re.IGNORECASE)
            clean_item = re.sub(r'\b\d+\s*(?:cartons?\s+of|bags?\s+of|boxes?\s+of|bottles?\s+of|units?\s+of)?\b', '', clean_item, flags=re.IGNORECASE)
            clean_item = clean_item.strip(" ,.:-")

            if not clean_item:
                clean_item = "Household Item"

            category = "Produce" if any(w in clean_item.lower() for w in ["apple", "banana", "fruit", "vegetable", "tomato"]) else (
                "Dairy" if any(w in clean_item.lower() for w in ["milk", "cheese", "yogurt", "butter"]) else "General"
            )

            return (
                "add_grocery_item",
                f"Add {quantity}x {clean_item.title()} to Groceries",
                {"name": clean_item.title(), "quantity": quantity, "category": category}
            )

        # Fallback
        return (
            "unknown_request",
            f"Process request: '{clause[:60]}...'",
            {"raw_clause": clause}
        )
