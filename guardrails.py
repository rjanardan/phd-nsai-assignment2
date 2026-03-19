from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import ValidationError
from models import TransferFundsRequest, DeleteResourceRequest

class GuardrailViolation(Exception):
    """Exception raised when a guardrail condition is violated."""
    def __init__(self, message: str, action: str):
        self.message = message
        self.action = action
        super().__init__(f"Guardrail Violation for '{action}': {message}")

class ActionHandler(ABC):
    """Base class for handling agent actions with type-safe guardrails."""
    
    @abstractmethod
    def validate_schema(self, data: Dict[str, Any]) -> Any:
        """Validate the input data against the action's Pydantic model."""
        pass

    @abstractmethod
    def pre_condition(self, request: Any, state: Dict[str, Any]) -> None:
        """Check conditions BEFORE the action is executed."""
        pass

    @abstractmethod
    def execute(self, request: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual action and return the new state."""
        pass

    @abstractmethod
    def post_condition(self, request: Any, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """Check conditions AFTER the action is executed."""
        pass

    def run(self, data: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate the action with guardrails."""
        try:
            # 1. Schema Validation (Type-Safe Guardrail)
            request = self.validate_schema(data)
            
            # 2. Pre-condition Check
            self.pre_condition(request, state)
            
            # 3. Execution
            new_state = self.execute(request, state.copy())
            
            # 4. Post-condition Check
            self.post_condition(request, state, new_state)
            
            return new_state
        except ValidationError as e:
            raise GuardrailViolation(str(e), data.get("action", "unknown"))
        except GuardrailViolation:
            raise
        except Exception as e:
            raise GuardrailViolation(f"Unexpected error: {str(e)}", data.get("action", "unknown"))

class TransferFundsHandler(ActionHandler):
    def validate_schema(self, data: Dict[str, Any]) -> TransferFundsRequest:
        return TransferFundsRequest(**data)

    def pre_condition(self, request: TransferFundsRequest, state: Dict[str, Any]) -> None:
        # Check if source account exists
        if request.from_account not in state["balances"]:
            raise GuardrailViolation(f"Source account {request.from_account} does not exist", "transfer_funds")
        
        # Check if destination account exists
        if request.to_account not in state["balances"]:
            raise GuardrailViolation(f"Destination account {request.to_account} does not exist", "transfer_funds")

        # Check for sufficient balance (Pre-condition)
        if state["balances"][request.from_account] < request.amount:
            raise GuardrailViolation(f"Insufficient funds in {request.from_account}", "transfer_funds")

    def execute(self, request: TransferFundsRequest, state: Dict[str, Any]) -> Dict[str, Any]:
        state["balances"][request.from_account] -= request.amount
        state["balances"][request.to_account] += request.amount
        return state

    def post_condition(self, request: TransferFundsRequest, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        # Post-condition: Balance must not be negative (Redundant but demonstrates the concept)
        if new_state["balances"][request.from_account] < 0:
            raise GuardrailViolation(f"Post-condition failed: {request.from_account} balance is negative", "transfer_funds")
        
        # Post-condition: Total money in the system must be conserved
        old_total = sum(old_state["balances"].values())
        new_total = sum(new_state["balances"].values())
        if abs(old_total - new_total) > 0.001:
             raise GuardrailViolation("Post-condition failed: Total funds not conserved", "transfer_funds")

class DeleteResourceHandler(ActionHandler):
    def validate_schema(self, data: Dict[str, Any]) -> DeleteResourceRequest:
        return DeleteResourceRequest(**data)

    def pre_condition(self, request: DeleteResourceRequest, state: Dict[str, Any]) -> None:
        # Pre-condition: Resource must exist
        if request.resource_id not in state["resources"]:
            raise GuardrailViolation(f"Resource {request.resource_id} does not exist", "delete_resource")
        
        # Pre-condition: Resource must not be 'protected'
        if state["resources"].get(request.resource_id, {}).get("protected", False):
            raise GuardrailViolation(f"Resource {request.resource_id} is protected and cannot be deleted", "delete_resource")

    def execute(self, request: DeleteResourceRequest, state: Dict[str, Any]) -> Dict[str, Any]:
        del state["resources"][request.resource_id]
        return state

    def post_condition(self, request: DeleteResourceRequest, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        # Post-condition: Resource must definitely be gone
        if request.resource_id in new_state["resources"]:
            raise GuardrailViolation(f"Post-condition failed: Resource {request.resource_id} still exists", "delete_resource")
