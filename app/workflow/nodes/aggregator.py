from app.workflow.state import ClaimState

def aggregator_node(state: ClaimState) -> dict:
    return {
        "final_result": {
            "claim_id": state["claim_id"],
            "segregation": state["segregation_result"],
            "identity": state["id_extraction"],
            "discharge_summary": state["discharge_extraction"],
            "itemized_bill": state["itemized_extraction"],
        }
    }
