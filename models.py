from pydantic import BaseModel, Field, validator
from typing import Literal

class TransferFundsRequest(BaseModel):
    action: Literal["transfer_funds"] = "transfer_funds"
    from_account: str = Field(..., description="Source account ID")
    to_account: str = Field(..., description="Destination account ID")
    amount: float = Field(..., gt=0, description="Amount to transfer (must be positive)")

    @validator("to_account")
    def accounts_must_be_different(cls, v, values):
        if "from_account" in values and v == values["from_account"]:
            raise ValueError("Source and destination accounts must be different")
        return v

class DeleteResourceRequest(BaseModel):
    action: Literal["delete_resource"] = "delete_resource"
    resource_id: str = Field(..., description="ID of the resource to delete")
