from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry.trace import get_current_span

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

from quotientai import QuotientAI
from quotientai.tracing import start_span

quotient = QuotientAI()
quotient.tracer.init(
    app_name="agno-search-app",
    environment="dev",
    instruments=[AgnoInstrumentor()],
)


@quotient.trace("agno-agent-ddgs-search")
def run_agno():
    # add additional span attributes
    span = get_current_span()
    span.set_attribute("mycustom.attr", "customvalue")

    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[DuckDuckGoTools()],
        markdown=True,
    )

    agent.print_response("What is currently trending on Twitter?")


if __name__ == "__main__":
    run_agno()
