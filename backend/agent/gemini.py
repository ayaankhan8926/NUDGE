import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.8-flash"


def get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to backend/.env"
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


def create_gemini_plan(goal):
    """
    Ask Gemini to convert a natural-language goal
    into a structured NUDGE execution plan.

    Gemini is ONLY responsible for planning.
    It does not execute tools or bypass the risk gate.
    """

    client = get_client()

    system_instruction = """
You are the planning brain of NUDGE,
a supervised workplace automation agent.

Your job is to understand the user's goal
and create a safe execution plan.

NUDGE can work with these tools:

1. Gmail
   - search emails
   - prepare email drafts
   - send emails

2. Calendar
   - read events
   - inspect meetings
   - prepare calendar actions

3. Sheets
   - read invoice/business data
   - analyze spreadsheet records

IMPORTANT SAFETY RULES:

- You are ONLY the planner.
- Never claim that an action has already been executed.
- Never send an email yourself.
- Never bypass human approval.
- External communication requires human approval.
- Destructive or irreversible actions must never
  be executed automatically.
- Prefer reading and analyzing data before
  proposing actions.
- Return ONLY valid JSON.

Return exactly this JSON structure:

{
  "goal_understanding": "short explanation",
  "steps": [
    {
      "step": 1,
      "tool": "gmail|calendar|sheets|none",
      "action": "action_name",
      "description": "what NUDGE should do"
    }
  ],
  "risk_actions": [
    "action_name"
  ],
  "requires_human_approval": true
}
"""

    prompt = f"""
User goal:

{goal}

Create the safest practical execution plan.
"""

    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=system_instruction + "\n\n" + prompt
    )

    raw_text = interaction.output_text.strip()

    try:
        return json.loads(raw_text)

    except json.JSONDecodeError:
        return {
            "goal_understanding": (
                "Gemini returned an invalid plan format."
            ),
            "steps": [],
            "risk_actions": [],
            "requires_human_approval": True,
            "raw_response": raw_text
        }