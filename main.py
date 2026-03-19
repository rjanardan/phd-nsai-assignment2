from guardrails import TransferFundsHandler, DeleteResourceHandler, GuardrailViolation
import json

def run_demonstration():
    # 1. Initial State (Mock Database)
    state = {
        "balances": {
            "Amit": 1000.0,
            "Bina": 500.0
        },
        "resources": {
            "res_001": {"name": "Database Backup", "protected": False},
            "res_002": {"name": "Production Root", "protected": True}
        }
    }

    print("--- INITIAL STATE ---")
    print(json.dumps(state, indent=2))
    print("\nStarting Guardrail Verification...\n")

    handlers = {
        "transfer_funds": TransferFundsHandler(),
        "delete_resource": DeleteResourceHandler()
    }

    # Test Cases: (Action Data, Expected Result)
    test_cases = [
        # 1. Valid Transfer
        {
            "action": "transfer_funds",
            "from_account": "Amit",
            "to_account": "Bina",
            "amount": 200.0
        },
        # 2. Invalid Schema: Negative Amount (Pydantic check)
        {
            "action": "transfer_funds",
            "from_account": "Amit",
            "to_account": "Bina",
            "amount": -50.0
        },
        # 3. Invalid Pre-condition: Insufficient Funds
        {
            "action": "transfer_funds",
            "from_account": "Bina",
            "to_account": "Amit",
            "amount": 2000.0
        },
        # 4. Valid Deletion
        {
            "action": "delete_resource",
            "resource_id": "res_001"
        },
        # 5. Invalid Pre-condition: Protected Resource
        {
            "action": "delete_resource",
            "resource_id": "res_002"
        },
        # 6. Invalid Pre-condition: Non-existent Resource
        {
            "action": "delete_resource",
            "resource_id": "res_404"
        }
    ]

    for i, action_data in enumerate(test_cases, 1):
        action_name = action_data.get("action")
        print(f"CASE {i}: Attempting '{action_name}'...")
        print(f"  Data: {action_data}")
        
        handler = handlers.get(action_name)
        if not handler:
            print(f"  FAILED: No handler for action '{action_name}'\n")
            continue

        try:
            new_state = handler.run(action_data, state)
            state = new_state
            print(f"  SUCCESS: Action executed. Current balances: {state['balances']}\n")
        except GuardrailViolation as e:
            print(f"  BLOCKER: {e.message}\n")
        except Exception as e:
            print(f"  ERROR: Unexpected error: {str(e)}\n")

    print("--- FINAL STATE ---")
    print(json.dumps(state, indent=2))

if __name__ == "__main__":
    run_demonstration()
