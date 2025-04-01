from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import traceback
from quotientai.exceptions import logger

from quotientai.resources.prompts import Prompt
from quotientai.resources.models import Model
from quotientai.resources.datasets import Dataset


@dataclass
class RunResult:
    """
    A run result represents each processed row in a dataset, when
    the prompt is run against a model with the parameters specified.
    """

    id: str
    input: str
    output: str
    # contains {"metric_name": value}
    values: dict
    created_at: datetime
    created_by: str

    context: Optional[str]
    expected: Optional[str]

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "values", self.values
        yield "created_at", self.created_at
        yield "created_by", self.created_by


@dataclass
class Run:
    # identifiers
    id: str

    # all inputs needed for a run
    # TODO: get prompt and dataset from their respective resources
    prompt: str
    dataset: str
    # TODO: get model from the models resource
    model: str
    parameters: dict
    # TODO: get metrics from the metrics resource
    metrics: List[str]

    # all outputs of a run, will get filled in as we progress
    status: str
    results: Optional[List[RunResult]] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "model", self.model
        yield "status", self.status

    def summarize(
        self,
        best_n: int = 3,
        worst_n: int = 3,
    ):
        """
        Calculate averages and std deviation from the metrics, and return a summary of the run.
        Also compare to the previous run if we had one for the same model and provider.

        Parameters
        ----------
        best_n : int
            The number of best performing rows to include in the summary.
        worst_n : int
            The number of worst performing rows to include in the summary.
        """
        # before the run is finished, we can't summarize it
        if not self.results:
            return None

        summary = {
            "run_id": self.id,
            "model": self.model,
            "parameters": self.parameters,
            "metrics": {
                metric: {
                    "avg": sum(result["values"][metric] for result in self.results)
                    / len(self.results),
                    "stddev": sum(
                        (
                            result["values"][metric]
                            - sum(result["values"][metric] for result in self.results)
                            / len(self.results)
                        )
                        ** 2
                        for result in self.results
                    )
                    / len(self.results),
                }
                for metric in self.metrics
            },
            "created_at": self.created_at,
        }

        def get_aggregate_score(result):
            """
            Get the aggregate score for a result. Used for sorting.
            """
            values = result["values"]
            scores = [
                float(value) if isinstance(value, bool) else value
                for value in values.values()
            ]
            return sum(scores) / len(scores)

        if best_n is not None and best_n > 0:
            summary[f"best_{best_n}"] = sorted(
                self.results, key=get_aggregate_score, reverse=True
            )[:best_n]

        if worst_n is not None and worst_n > 0:
            summary[f"worst_{worst_n}"] = sorted(
                self.results, key=get_aggregate_score, reverse=False
            )[:worst_n]

        return summary


class RunsResource:
    """
    A resource for interacting with models in the QuotientAI API.
    """

    def __init__(self, client) -> None:
        self._client = client

    def list(self) -> List[Run]:
        response = self._client._get("/runs")

        runs = []
        for run in response:
            runs.append(
                Run(
                    id=run["id"],
                    prompt=run["prompt"],
                    dataset=run["dataset"],
                    model=run["model"],
                    parameters=run["parameters"],
                    metrics=run["metrics"],
                    status=run["status"],
                    results=run["results"],
                    created_at=(
                        datetime.fromisoformat(run["created_at"])
                        if run["created_at"] is not None
                        else None
                    ),
                    finished_at=(
                        datetime.fromisoformat(run["finished_at"])
                        if run["finished_at"] is not None
                        else None
                    ),
                )
            )

        return runs

    def get(self, run_id: str) -> Run:
        response = self._client._get(f"/runs/{run_id}")

        run = Run(
            id=response["id"],
            prompt=response["prompt"],
            dataset=response["dataset"],
            model=response["model"],
            parameters=response["parameters"],
            metrics=response["metrics"],
            status=response["status"],
            results=response["results"],
            created_at=(
                datetime.fromisoformat(response["created_at"])
                if response["created_at"] is not None
                else None
            ),
            finished_at=(
                datetime.fromisoformat(response["finished_at"])
                if response["finished_at"] is not None
                else None
            ),
        )
        return run

    def create(
        self,
        prompt: Prompt,
        dataset: Dataset,
        model: Model,
        parameters: dict,
        metrics: List[str],
    ) -> Run:
        data = {
            "prompt_id": prompt.id,
            "dataset_id": dataset.id,
            "model_id": model.id,
            "parameters": parameters,
            "metrics": metrics,
        }
        response = self._client._post("/runs", data=data)
        run = Run(
            id=response["id"],
            prompt=prompt.id,
            dataset=dataset.id,
            model=model.id,
            parameters=parameters,
            metrics=metrics,
            status=response["status"],
            created_at=datetime.fromisoformat(response["created_at"]),
            finished_at=datetime.fromisoformat(response["finished_at"]),
        )
        return run

    # create a method to compare two or more runs across the same dataset
    # and either show scores on average for a prompt, or for a model.
    # all done here in the runs resource, as it's the most logical place
    def compare(
        self,
        runs: List[Run],
    ):
        # ensure the datasets are the same, and then compare the runs.
        if len(set(run.dataset for run in runs)) > 1:
            logger.error(f"all runs must be on the same dataset in order to compare them\n{traceback.format_exc()}")
            return None
        # prompts can be the different or models can be the different, but not both
        # inference parameteres can be different, but not metrics, in order to compare
        # evenly across the runs
        if (
            len(set(run.prompt for run in runs)) > 1
            and len(set(run.model for run in runs)) > 1
        ):
            logger.error(f"all runs must be on the same prompt or model in order to compare them\n{traceback.format_exc()}")
            return None
        # compare the runs. a comparison will show the average scores for each metric
        # across all runs, and the standard deviation for each metric, using their summaries.
        #
        # it will also highlight which run is the best and which is the worst.
        # if there are only two runs, it will also show the difference between the two.
        # if there are more than two runs, it will show the difference in scores between
        # each run sorted by creation date.
        summaries = [run.summarize() for run in runs]
        if len(runs) == 2:
            comparison = {
                metric: {
                    "avg": summaries[0]["metrics"][metric]["avg"]
                    - summaries[1]["metrics"][metric]["avg"],
                    "stddev": summaries[0]["metrics"][metric]["stddev"],
                }
                for metric in runs[0].metrics
            }
        elif len(runs) > 2:
            comparison = {
                run.id: {
                    metric: {
                        "avg": summaries[0]["metrics"][metric]["avg"]
                        - summaries[1]["metrics"][metric]["avg"],
                        "stddev": summaries[0]["metrics"][metric]["stddev"],
                    }
                    for metric in runs[0].metrics
                }
                for run in runs
            }
        else:
            comparison = None

        return comparison


class AsyncRunsResource:
    """
    An asynchronous resource for interacting with models in the QuotientAI API.
    """

    def __init__(self, client) -> None:
        self._client = client

    async def list(self) -> List[Run]:
        response = await self._client._get("/runs")

        runs = []
        for run in response:
            runs.append(
                Run(
                    id=run["id"],
                    prompt=run["prompt"],
                    dataset=run["dataset"],
                    model=run["model"],
                    parameters=run["parameters"],
                    metrics=run["metrics"],
                    status=run["status"],
                    results=run["results"],
                    created_at=(
                        datetime.fromisoformat(run["created_at"])
                        if run["created_at"] is not None
                        else None
                    ),
                    finished_at=(
                        datetime.fromisoformat(run["finished_at"])
                        if run["finished_at"] is not None
                        else None
                    ),
                )
            )

        return runs

    async def get(self, run_id: str) -> Run:
        response = await self._client._get(f"/runs/{run_id}")

        run = Run(
            id=response["id"],
            prompt=response["prompt"],
            dataset=response["dataset"],
            model=response["model"],
            parameters=response["parameters"],
            metrics=response["metrics"],
            status=response["status"],
            results=response["results"],
            created_at=(
                datetime.fromisoformat(response["created_at"])
                if response["created_at"] is not None
                else None
            ),
            finished_at=(
                datetime.fromisoformat(response["finished_at"])
                if response["finished_at"] is not None
                else None
            ),
        )
        return run

    async def create(
        self,
        prompt: Prompt,
        dataset: Dataset,
        model: Model,
        parameters: dict,
        metrics: List[str],
    ) -> Run:
        data = {
            "prompt_id": prompt.id,
            "dataset_id": dataset.id,
            "model_id": model.id,
            "parameters": parameters,
            "metrics": metrics,
        }
        response = await self._client._post("/runs", data=data)
        run = Run(
            id=response["id"],
            prompt=prompt.id,
            dataset=dataset.id,
            model=model.id,
            parameters=parameters,
            metrics=metrics,
            status=response["status"],
            created_at=datetime.fromisoformat(response["created_at"]),
            finished_at=datetime.fromisoformat(response["finished_at"]),
        )
        return run

    # create a method to compare two or more runs across the same dataset
    # and either show scores on average for a prompt, or for a model.
    # all done here in the runs resource, as it's the most logical place
    async def compare(
        self,
        runs: List[Run],
    ):
        # ensure the datasets are the same, and then compare the runs.
        if len(set(run.dataset for run in runs)) > 1:
            logger.error(f"all runs must be on the same dataset in order to compare them\n{traceback.format_exc()}")
            return None
        # prompts can be the different or models can be the different, but not both
        # inference parameteres can be different, but not metrics, in order to compare
        # evenly across the runs
        if (
            len(set(run.prompt for run in runs)) > 1
            and len(set(run.model for run in runs)) > 1
        ):
            logger.error(f"all runs must be on the same prompt or model in order to compare them\n{traceback.format_exc()}")
            return None

        # compare the runs. a comparison will show the average scores for each metric
        # across all runs, and the standard deviation for each metric, using their summaries.
        #
        # it will also highlight which run is the best and which is the worst.
        # if there are only two runs, it will also show the difference between the two.
        # if there are more than two runs, it will show the difference in scores between
        # each run sorted by creation date.
        summaries = [run.summarize() for run in runs]
        if len(runs) == 2:
            comparison = {
                metric: {
                    "avg": summaries[0]["metrics"][metric]["avg"]
                    - summaries[1]["metrics"][metric]["avg"],
                    "stddev": summaries[0]["metrics"][metric]["stddev"],
                }
                for metric in runs[0].metrics
            }
        elif len(runs) > 2:
            comparison = {
                run.id: {
                    metric: {
                        "avg": summaries[0]["metrics"][metric]["avg"]
                        - summaries[1]["metrics"][metric]["avg"],
                        "stddev": summaries[0]["metrics"][metric]["stddev"],
                    }
                    for metric in runs[0].metrics
                }
                for run in runs
            }
        else:
            comparison = None

        return comparison
