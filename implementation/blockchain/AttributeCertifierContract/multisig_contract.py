from pyteal import *

## Contract logic
messageID = Bytes("msg_id")
IPFSLink = Bytes("ipfs_link")

# Create an expression to store 0 in the `Count` global variable and return 1
handle_creation = Seq(
      App.globalPut(messageID, Int(0)),
      App.globalPut(IPFSLink, Int(0)), 
      Approve(),
      )

handle_delete = If(
    Txn.sender() == Global.creator_address()
    ).Then(
        Approve()
    ).Else(Reject())

# Main router class
def getRouter():
    router = Router(
        # Name of the contract
        "my-first-router",
        # What to do for each on-complete type when no arguments are passed (bare call)
        BareCallActions(
            # On create only, just approve
            no_op=OnCompleteAction.create_only(handle_creation),
            # Always let creator update/delete but only by the creator of this contract
            update_application=OnCompleteAction.always(Reject()),
            delete_application=OnCompleteAction.always(handle_delete),
            # No local state, don't bother handling it.
            close_out=OnCompleteAction.never(),
            opt_in=OnCompleteAction.never(),
        ),
    )


    @router.method(no_op=CallConfig.CALL)
    def on_save(message_id: abi.String, ipfs_link: abi.String) -> Expr:
        return Seq(
            App.globalPut(messageID, message_id.get()),
            App.globalPut(IPFSLink, ipfs_link.get()),
        )

    return router
