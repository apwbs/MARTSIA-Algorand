import json
from pyteal import *
pragma(compiler_version="^0.23.0")
CONTRACT_VERSION = 8

router = Router(
    # Name of the contract
    "box-demo",
    # What to do for each on-complete type when no arguments are passed (bare call)
    BareCallActions(
        no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE)
    ),
)


@router.method(no_op=CallConfig.CALL)
def put(value: abi.String) -> Expr:
    """Write to a box"""
    return Seq(
        App.box_put(Txn.sender(), value.get()),
        Approve(),
    )


@router.method(no_op=CallConfig.CALL)
def read() -> Expr:
    """Read from a box"""
    return Seq(
        boxint := App.box_get(Txn.sender()),
        Log(boxint.value()),
    )


@router.method(no_op=CallConfig.CALL)
def length() -> Expr:
    """Get the length a box value"""
    return Seq(
        bt := App.box_length(Txn.sender()),
        Log(Itob(bt.value())),
    )


@router.method(no_op=CallConfig.CALL)
def delete() -> Expr:
    """Delete a box"""
    return Seq(
        Log(Itob(App.box_delete(Txn.sender()))),
    )


if __name__ == "__main__":
    approval, clearstate, contract = router.compile_program(version=CONTRACT_VERSION)

    with open("approve-box.teal", "w") as f:
        f.write(approval)

    with open("clear-box.teal", "w") as f:
        f.write(clearstate)

    with open("contract.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
