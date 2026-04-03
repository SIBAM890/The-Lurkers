from langgraph.graph import StateGraph
from core.logger import get_logger

logger = get_logger()

def run_agent(graph: StateGraph, initial_state: dict, ps_id: str) -> dict:
    logger.info(f"Starting agent {ps_id}")
    try:
        compiled = graph.compile()
        result = compiled.invoke(initial_state)
        logger.info(f"Agent {ps_id} completed. Status: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Agent {ps_id} failed: {str(e)}")
        return {**initial_state, "status": "error", "errors": [str(e)]}
