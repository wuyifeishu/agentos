"""Orchestration module — Graph orchestrator, A2A routing, graph executor, parallel scheduler, swarm coordinator, distributed orchestration, task decomposer"""

from agentos.orchestration.graph import (
    GraphOrchestrator,
    GraphNode,
    GraphEdge,
)
from agentos.orchestration.a2a_router import (
    A2ARouter,
    AgentCard as RouterAgentCard,
    Task as RouterTask,
    TaskResult,
    TaskStatus,
)
from agentos.orchestration.graph_executor import (
    AgentGraph,
    GraphRecipe,
    GraphNodeState,
    GraphResult,
)
from agentos.orchestration.parallel import (
    ParallelExecutor,
    RunResult,
)
from agentos.swarm.coordinator import (
    SwarmCoordinator,
    SwarmAgentInfo as AgentInfo,
    SwarmTask,
    SwarmTopology,
    SwarmMessage,
    MessageBus,
    TaskPriority,
    TaskStatus as SwarmTaskStatus,
    TaskAllocator,
    ConflictResolver,
    ConflictType,
    SwarmAgentRole as AgentRole,
)
from agentos.orchestration.task_decomposer import (
    TaskDecomposer,
    TaskDAG,
    TaskNode,
    TaskEdge,
    TaskNodeStatus,
    DecompositionStrategy,
    DecompositionTrace,
    create_decomposer,
)

# Distributed orchestration (optional: requires ray)
try:
    from agentos.orchestration.distributed import (
        DistSwarmCoordinator,
        DistSwarmConfig,
        DistTaskQueue,
        DistTaskRecord,
        DistTaskStatus,
        CrossNodeBus,
        CrossNodeMailbox,
        RayAgentActor,
        AgentPlacementSpec,
        AgentStatus as DistAgentStatus,
        PlacementStrategy,
        quick_start,
    )
    _HAS_DISTRIBUTED = True
except ImportError:
    DistSwarmCoordinator = None  # type: ignore
    DistSwarmConfig = None
    DistTaskQueue = None
    DistTaskRecord = None
    DistTaskStatus = None
    CrossNodeBus = None
    CrossNodeMailbox = None
    RayAgentActor = None
    AgentPlacementSpec = None
    DistAgentStatus = None
    PlacementStrategy = None
    quick_start = None
    _HAS_DISTRIBUTED = False

__all__ = [
    "GraphOrchestrator",
    "GraphNode",
    "GraphEdge",
    "A2ARouter",
    "RouterAgentCard",
    "RouterTask",
    "TaskResult",
    "TaskStatus",
    "AgentGraph",
    "GraphRecipe",
    "GraphNodeState",
    "GraphResult",
    "ParallelExecutor",
    "RunResult",
    # Swarm Coordinator v2
    "SwarmCoordinator",
    "AgentInfo",
    "AgentRole",
    "SwarmTask",
    "SwarmTopology",
    "TaskPriority",
    "SwarmTaskStatus",
    "TaskAllocator",
    "ConflictResolver",
    "ConflictType",
    "MessageBus",
    "SwarmMessage",
    # Task Decomposer v2 (v1.14.7)
    "TaskDecomposer",
    "TaskDAG",
    "TaskNode",
    "TaskEdge",
    "TaskNodeStatus",
    "DecompositionStrategy",
    "DecompositionTrace",
    "create_decomposer",
    # Distributed Orchestration (v1.14.2, optional)
    "DistSwarmCoordinator",
    "DistSwarmConfig",
    "DistTaskQueue",
    "DistTaskRecord",
    "DistTaskStatus",
    "CrossNodeBus",
    "CrossNodeMailbox",
    "RayAgentActor",
    "AgentPlacementSpec",
    "DistAgentStatus",
    "PlacementStrategy",
    "quick_start",
]
