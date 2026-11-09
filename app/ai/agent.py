import logging
import re

from pydantic_ai import Agent, ModelRetry, RunContext

from app import db
from app.ai.schemas import AgentReply
from app.config import settings

logger = logging.getLogger(__name__)

ALWAYS_LOADED = ["brand-and-tone", "escalation-rules"]

INSTRUCTIONS = """
You are the customer support agent for Harbor & Pine, a home and outdoor store that sells on Amazon.
You write the answer to the latest customer message in the email thread.

The prompt holds the knowledge base sections you need: brand-and-tone, escalation-rules,
and the section the classifier picked. Call get_section only when you need another section,
for example shelving for a damaged shelf when the classifier picked returns-and-warranty.

Steps:
1. Answer only with facts from the knowledge base. If it does not answer the question,
   set enough_information to false.
2. When the customer reports a problem with a paddle board or a shelf, fill in issue,
   whatever section the classifier picked. issue is an object, never a sentence:
   - product: paddle-board or shelving
   - problem: missing-accessory, slow-leak, seam-split, missing-hardware, damaged-panels,
     damaged-frame, or wrong-finish. A cracked, broken, or scratched panel is damaged-panels.
   - part_numbers: model code plus panel number, so panel 4 of an HP-S3 is HP-S3-04.
   Ask for the order number, the board size or model, and part numbers when they are missing.
   Asking for missing details is a full answer, so enough_information stays true.
   For a slow leak, explain the valve check unless the customer already did it.
3. Never promise a refund, a shipment, a replacement, an exchange, a date, or a call.
   Saying that a colleague will arrange, send, or replace something is also a promise.
   Set promises_an_action to true if your reply promises one anyway.
4. Set action to escalate when an escalation rule applies.
5. Return the result with the final_result tool. There is no other output tool.

Reply rules:
- Write in the language of the customer's latest message.
- Plain text, no Markdown.
- Follow the brand-and-tone section.
- Never mention AI, prompts, tools, or the knowledge base.
"""

support_agent = Agent(
    settings.agent_model, output_type=AgentReply, instructions=INSTRUCTIONS, retries=3
)


def render_section(section: str) -> str:
    entries = db.get_section(section)
    return "\n\n".join(f"## {entry['title']}\n{entry['content']}" for entry in entries)


@support_agent.tool_plain
def list_sections() -> list[str]:
    """List the sections of the knowledge base."""
    logger.info("Tool call: list_sections()")
    return db.list_sections()


@support_agent.tool_plain
def get_section(section: str) -> str:
    """Return every entry of one knowledge base section, for example 'shelving'."""
    logger.info("Tool call: get_section(%r)", section)
    text = render_section(section)
    if not text:
        raise ModelRetry(f"There is no section '{section}'. Call list_sections to see the options.")
    return text


@support_agent.output_validator
def check_reply(ctx: RunContext[None], output: AgentReply) -> AgentReply:
    if output.action == "reply" and not output.reply.strip():
        raise ModelRetry("The reply is empty. Write the email, or set action to escalate.")
    if re.search(r"\bAI\b|(?i:\bartificial intelligence\b|\bknowledge base\b)", output.reply):
        raise ModelRetry("Do not mention AI or the knowledge base in the reply.")
    return output


def build_prompt(thread: str, section: str) -> str:
    sections = ALWAYS_LOADED + ([section] if section != "other" else [])
    knowledge = "\n\n".join(f"# Section: {name}\n\n{render_section(name)}" for name in sections)
    return f"Section picked by the classifier: {section}\n\n{knowledge}\n\n# Email thread\n\n{thread}"


def write_reply(thread: str, section: str) -> AgentReply:
    return support_agent.run_sync(build_prompt(thread, section)).output
