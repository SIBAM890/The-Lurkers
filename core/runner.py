from langgraph.graph import StateGraph
from core.logger import get_logger
from langgraph.checkpoint.memory import MemorySaver
import uuid

logger = get_logger()

# Global checkpointer for persistence across endpoints
global_memory = MemorySaver()

def run_agent(graph: StateGraph, initial_state: dict, ps_id: str, thread_id: str = None, interrupt_before: list = None) -> dict:
    logger.info(f"Starting agent {ps_id}")
    run_id = uuid.uuid4()
    try:
        if thread_id or interrupt_before:
            compiled = graph.compile(checkpointer=global_memory, interrupt_before=interrupt_before)
            config = {"configurable": {"thread_id": thread_id if thread_id else ps_id}, "run_id": run_id}
            result = compiled.invoke(initial_state, config)
        else:
            # Run statelessly just like before for PS-01 and PS-02
            compiled = graph.compile()
            result = compiled.invoke(initial_state, {"run_id": run_id})
            
        logger.info(f"Agent {ps_id} completed. Status: {result.get('status')}")
        return {"agent_state": result, "run_id": str(run_id)}
    except Exception as e:
        logger.error(f"Agent {ps_id} failed: {str(e)}")
        return {"agent_state": {**initial_state, "status": "error", "errors": [str(e)]}, "run_id": str(run_id)}

def resume_agent(graph: StateGraph, thread_id: str, ps_id: str, update_state: dict = None) -> dict:
    logger.info(f"Resuming agent {ps_id} for thread {thread_id}")
    run_id = uuid.uuid4()
    try:
        compiled = graph.compile(checkpointer=global_memory)
        config = {"configurable": {"thread_id": thread_id}, "run_id": run_id}
        
        if update_state:
            compiled.update_state(config, update_state)
            
        result = compiled.invoke(None, config)
        return {"agent_state": result, "run_id": str(run_id)}
    except Exception as e:
        logger.error(f"Agent {ps_id} resume failed: {str(e)}")
        return {"agent_state": {"status": "error", "errors": [str(e)]}, "run_id": str(run_id)}
