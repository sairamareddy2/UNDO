"""
Google Gemini Integration Adapter (Official Google GenAI SDK: google-genai)

Connects to the Gemini API using Google AI Studio API key.
Derives structured action proposals using Pydantic structured output schemas.
Never hardcodes or prints API keys. All proposals are sent to the deterministic
policy engine before any state execution.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_INSTRUCTION = (
    "You are the Action Intent Planner for UNDO, an Alexa+ action governance system. "
    "Your objective is to parse the user's natural language command into structured action proposals.\n\n"
    "Available action types and parameter schemas:\n"
    "1. 'add_grocery_item': parameters {'name': str, 'quantity': int, 'category': str}\n"
    "2. 'remove_grocery_item': parameters {'item_id': int, 'name': str}\n"
    "3. 'create_reminder': parameters {'title': str, 'remind_at': str, 'priority': 'low'|'medium'|'high'}\n"
    "4. 'delete_reminder': parameters {'reminder_id': int, 'title': str}\n"
    "5. 'set_door_lock': parameters {'door_id': 'front_door'|'back_door'|'garage_entry', 'target_state': 'locked'|'unlocked'}\n\n"
    "If the user asks for destructive, high-risk, or disallowed actions (e.g. wiping database, "
    "transferring money, deleting accounts), propose the action with its descriptive type "
    "(e.g. 'wipe_database', 'transfer_funds', 'delete_account') so the downstream deterministic policy "
    "engine can block it.\n"
    "If a request is ambiguous or unknown, use action_type 'unknown_request'."
)


class ActionParameters(BaseModel):
    name: Optional[str] = Field(None, description="Item or target name")
    quantity: Optional[int] = Field(None, description="Item quantity")
    category: Optional[str] = Field(None, description="Item category")
    door_id: Optional[str] = Field(None, description="Identifier for door lock")
    target_state: Optional[str] = Field(None, description="Target state for lock (locked/unlocked)")
    title: Optional[str] = Field(None, description="Reminder title")
    remind_at: Optional[str] = Field(None, description="Reminder time or ISO string")
    priority: Optional[str] = Field(None, description="Reminder priority (low/medium/high)")
    target: Optional[str] = Field(None, description="Target entity for destructive action")
    item_id: Optional[int] = Field(None, description="ID of item to delete")
    reminder_id: Optional[int] = Field(None, description="ID of reminder to delete")
    amount: Optional[float] = Field(None, description="Transaction amount")
    currency: Optional[str] = Field(None, description="Transaction currency")
    confirmation: Optional[bool] = Field(None, description="Confirmation flag")
    raw_prompt: Optional[str] = Field(None, description="Raw user prompt")


class ProposedAction(BaseModel):
    action_type: str = Field(..., description="Action capability identifier")
    title: str = Field(..., description="Concise human-readable description of the action")
    parameters: ActionParameters = Field(default_factory=ActionParameters, description="Parameters object")


class ActionPlanProposal(BaseModel):
    actions: List[ProposedAction] = Field(default_factory=list, description="Ordered list of proposed action steps")
    reasoning: Optional[str] = Field(None, description="Brief explanation of user intent")


class GeminiAdapter:
    """
    Adapter using the official google-genai SDK to interact with Google Gemini models.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Read API key strictly from environment or settings; never log or print it
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model = model or os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3-flash-preview"
        self._client: Optional[genai.Client] = None

    def is_available(self) -> bool:
        """Returns True if a non-empty Gemini API key is configured."""
        return bool(self._api_key and str(self._api_key).strip())

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self.is_available():
                raise ValueError("GEMINI_API_KEY is not configured.")
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate_action_proposals(self, prompt: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Invokes Gemini with structured output constraints to propose action candidates.
        Returns a list of tuples: (action_type, title, parameters).
        Returns an empty list on failure or if unconfigured, triggering fallback.
        """
        if not self.is_available():
            return []

        try:
            client = self._get_client()
            config = types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ActionPlanProposal,
                temperature=0.1,
            )

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            # Extract structured response
            proposal: Optional[ActionPlanProposal] = None
            if hasattr(response, "parsed") and isinstance(response.parsed, ActionPlanProposal):
                proposal = response.parsed
            elif hasattr(response, "text") and response.text:
                proposal = ActionPlanProposal.model_validate_json(response.text)

            if not proposal or not proposal.actions:
                return []

            # Format into validated candidate tuples
            candidates: List[Tuple[str, str, Dict[str, Any]]] = []
            for item in proposal.actions:
                action_type = str(item.action_type).strip()
                title = str(item.title).strip()
                if isinstance(item.parameters, ActionParameters):
                    params = item.parameters.model_dump(exclude_none=True)
                elif isinstance(item.parameters, dict):
                    params = item.parameters
                else:
                    params = {}
                candidates.append((action_type, title, params))

            return candidates

        except (ValidationError, json.JSONDecodeError) as e:
            logger.warning(f"Gemini returned malformed structured output: {e}")
            return []
        except Exception as e:
            logger.warning(f"Gemini API request error: {e}")
            return []


# Global singleton instance
gemini_adapter = GeminiAdapter()
