from pprint import pprint

from accounts_payable_agent.agents.orchestrator import (
    Orchestrator
)


def demo():

    orch = Orchestrator()

    sample_invoice = {

        "filename":
            "INV-1001.pdf",

        "vendor":
            "Acme Ltd",

        "amount":
            250.0,

        "currency":
            "USD",

        "date":
            "2026-05-21",

        "po_number":
            "PO-1234"
    }

    try:

        result = (
            orch.run(
                sample_invoice
            )
        )

        print("\n==========")
        print("FINAL RESULT")
        print("==========\n")

        pprint(result)

        print("\n==========")
        print("WORKFLOW STATUS")
        print("==========\n")

        print(
            result.get(
                "workflow_status"
            )
        )

        print("\n==========")
        print("AUDIT LOG")
        print("==========\n")

        pprint(
            result.get(
                "audit_log",
                []
            )
        )

        if (
            result.get(
                "decision"
            )
        ):

            print(
                "\nDecision:",
                result[
                    "decision"
                ]
            )

    except Exception as e:

        print(
            "\nWorkflow failed:"
        )

        print(
            str(e)
        )


if __name__ == "__main__":

    demo()