import time
from dataclasses import dataclass

from pydantic_ai.exceptions import ModelConnectionError, ModelRateLimitError
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from app.ai.decide import decide
from app.ai.schemas import Decision
from evals.golden_emails import GOLDEN_EMAILS

RATE_LIMIT_ATTEMPTS = 4
RATE_LIMIT_WAIT_SECONDS = 30


@dataclass
class SectionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.section == ctx.expected_output["section"]


@dataclass
class ActionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.action == ctx.expected_output["action"]


def run_pipeline(email: str) -> Decision:
    for attempt in range(RATE_LIMIT_ATTEMPTS):
        try:
            return decide(email)
        except (ModelRateLimitError, ModelConnectionError):
            if attempt == RATE_LIMIT_ATTEMPTS - 1:
                raise
            time.sleep(RATE_LIMIT_WAIT_SECONDS)


dataset = Dataset(
    name="golden-emails",
    cases=[
        Case(
            name=case["name"],
            inputs=case["email"],
            expected_output={"section": case["section"], "action": case["action"]},
        )
        for case in GOLDEN_EMAILS
    ],
    evaluators=[SectionMatches(), ActionMatches()],
)

if __name__ == "__main__":
    report = dataset.evaluate_sync(run_pipeline, max_concurrency=1)
    report.print(include_input=False, include_output=True, include_durations=False)