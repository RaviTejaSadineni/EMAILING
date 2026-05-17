from pydantic import BaseModel


class StageDefinition(BaseModel):
    stage: int
    name: str
    description: str


class LifecycleOverview(BaseModel):
    contracts_per_stage: dict[str, int]
    avg_time_per_stage: dict[str, float]


class BottleneckAnalysis(BaseModel):
    bottlenecks: list[dict]


class SLABreachReport(BaseModel):
    items: list[dict]


class StageMetrics(BaseModel):
    metrics: dict[str, dict]


class NegotiationAnalysis(BaseModel):
    average_rounds: float
    most_negotiated_clauses: list[dict]
