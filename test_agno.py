from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.yfinance import YFinanceTools

from quotientai import QuotientAI

quotient = QuotientAI()

@quotient.trace()
def main():
    reasoning_agent = Agent(
        model=Claude(id="claude-sonnet-4-20250514"),
        tools=[
            YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
        ],
        instructions="Use tables to display data.",
        markdown=True,
    )

    reasoning_agent.print_response("What is the stock price of Apple?")

if __name__ == "__main__":
    main()