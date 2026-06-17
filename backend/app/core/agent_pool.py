from app.core.adk_runner import ADKRunner


class AgentPool:

    def __init__(self):

        self.agent_count = 5

    def classify_page(
        self,
        page_number: int,
        text: str
    ):

        results = []

        for _ in range(self.agent_count):

            runner = ADKRunner()

            result = runner.classify_page(
                page_number=page_number,
                text=text
            )

            results.append(result)

        return results