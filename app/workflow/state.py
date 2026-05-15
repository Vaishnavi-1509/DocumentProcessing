from typing import TypedDict, Any

class ClaimState(TypedDict):
    claim_id: str
    page_images: list[str]
    segregation_result: dict
    id_extraction: dict[str, Any]
    discharge_extraction: dict[str, Any]
    itemized_extraction: dict[str, Any]
    final_result: dict[str, Any]
