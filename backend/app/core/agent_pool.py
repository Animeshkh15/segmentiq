from concurrent.futures import ThreadPoolExecutor

from app.core.adk_runner import ADKRunner


class AgentPool:

    def __init__(self):

        self.agent_count = 5

    def _run_agent(
        self,
        page_number: int,
        text: str
    ):

        print(
            f"Agent started for page {page_number}"
        )

        runner = ADKRunner()

        result = runner.classify_page(
            page_number=page_number,
            text=text
        )

        print(
            f"Agent finished for page {page_number}"
        )

        return result

    def classify_page(
        self,
        page_number: int,
        text: str
    ):

        print(
            f"Starting {self.agent_count} parallel agents for page {page_number}"
        )

        with ThreadPoolExecutor(
            max_workers=self.agent_count
        ) as executor:

            futures = [

                executor.submit(
                    self._run_agent,
                    page_number,
                    text
                )

                for _ in range(self.agent_count)
            ]

            results = [

                future.result()

                for future in futures
            ]

        print(
            f"Completed {self.agent_count} agents for page {page_number}"
        )

        return results