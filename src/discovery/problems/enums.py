from enum import StrEnum


class TaskFamily(StrEnum):
    OPTIMIZATION = "optimization"
    SEARCH = "search"
    SAMPLING = "sampling"
    ESTIMATION = "estimation"
    INFERENCE = "inference"
    SIMULATION = "simulation"
    PREDICTION = "prediction"
    CLASSIFICATION = "classification"
    CONTROL = "control"
    INVERSE_PROBLEM = "inverse_problem"
    LINEAR_SYSTEM = "linear_system"
    EIGENPROBLEM = "eigenproblem"
    SPECTRAL_PROBLEM = "spectral_problem"
    DIFFERENTIAL_EQUATION = "differential_equation"
    STOCHASTIC_PROCESS = "stochastic_process"
    GRAPH_PROBLEM = "graph_problem"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    PLANNING = "planning"
    DYNAMICAL_SYSTEM = "dynamical_system"
    RARE_EVENT = "rare_event"
    INTEGRATION = "integration"
    COUNTING = "counting"
    OTHER = "other"
    UNKNOWN = "unknown"


class EvidenceKind(StrEnum):
    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    APPENDIX = "appendix"
    EQUATION = "equation"
    FIGURE = "figure"
    TABLE = "table"
    SUPPLEMENT = "supplement"
    OTHER = "other"


class ExtractionMethod(StrEnum):
    HUMAN = "human"
    LLM = "llm"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    IMPORTED = "imported"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    HUMAN_REVIEWED = "human_reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
