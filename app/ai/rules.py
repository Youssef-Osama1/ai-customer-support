import re

from app.ai.schemas import Issue

CUSTOMER_STEPS = {"valve-check", "ask-details"}
ORDER_NUMBER = re.compile(r"\b\d{3}-\d{7}-\d{7}\b")


def find_order_number(thread: str) -> str | None:
    match = ORDER_NUMBER.search(thread)
    return match.group() if match else None


def resolve_issue(issue: Issue, thread: str = "") -> str:
    """Decide the next step for a reported problem. The model reports, Python decides."""
    if not issue.order_number:
        issue = issue.model_copy(update={"order_number": find_order_number(thread)})
    step = next_step(issue)
    if step not in CUSTOMER_STEPS | {"escalate"} and not issue.order_number:
        return "ask-details"
    return step


def next_step(issue: Issue) -> str:
    if issue.product == "paddle-board":
        if issue.problem == "missing-accessory":
            return "ship-part"
        if issue.problem == "slow-leak":
            if not issue.valve_checked:
                return "valve-check"
            if issue.days_since_delivery is None:
                return "ask-details"
            return "new-board" if issue.days_since_delivery <= 30 else "patch-kit"
    if issue.product == "shelving":
        if issue.problem == "missing-hardware":
            return "ship-hardware-kit"
        if issue.problem == "wrong-finish":
            return "exchange"
        if issue.problem == "damaged-frame":
            return "full-replacement"
        if issue.problem == "damaged-panels":
            if not issue.part_numbers:
                return "ask-details"
            return "ship-panels" if len(issue.part_numbers) <= 2 else "full-replacement"
    return "escalate"