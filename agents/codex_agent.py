"""
CodexAgent — core agentic loop wrapping the OpenAI Responses API.

Uses tool-use to let Codex inspect real files and diffs before producing
structured output. This mirrors how you'd deploy Codex in a production
SDLC workflow: the model reasons about actual code, not synthetic prompts.
"""

import json
import os
from typing import Any

from openai import OpenAI
from rich.console import Console

console = Console()

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("CODEX_MODEL", "gpt-4.1")
MAX_TOOL_ROUNDS = 10  # safety cap on the agentic loop


class CodexAgent:
    """
    Thin wrapper around the OpenAI Responses API that runs a tool-use loop
    until the model produces a final text response.

    Parameters
    ----------
    tools : list[dict]
        OpenAI tool definitions (function schemas).
    tool_handlers : dict[str, callable]
        Mapping of tool name → Python function to execute locally.
    system_prompt : str
        Role/context prompt for the agent.
    model : str
        Model ID to use (default: gpt-4.1).
    """

    def __init__(
        self,
        tools: list[dict],
        tool_handlers: dict[str, Any],
        system_prompt: str,
        model: str = DEFAULT_MODEL,
    ):
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.tools = tools
        self.tool_handlers = tool_handlers
        self.system_prompt = system_prompt
        self.model = model

    def run(self, user_message: str) -> str:
        """
        Run the agentic loop for a given user message.

        Returns the final text response from the model.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        for round_num in range(MAX_TOOL_ROUNDS):
            console.log(f"[dim]Agent round {round_num + 1}[/dim]")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
            )

            message = response.choices[0].message

            # No tool calls — model is done
            if not message.tool_calls:
                return message.content or ""

            # Append assistant message with tool calls
            messages.append(message)

            # Execute each tool call and append results
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                console.log(f"[cyan]Tool call:[/cyan] {tool_name}({tool_args})")

                if tool_name not in self.tool_handlers:
                    result = f"Error: unknown tool '{tool_name}'"
                else:
                    try:
                        result = self.tool_handlers[tool_name](**tool_args)
                    except Exception as exc:
                        result = f"Error executing {tool_name}: {exc}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )

        return "Error: agent exceeded maximum tool rounds without producing a final response."
