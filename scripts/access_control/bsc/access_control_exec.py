from brownie import rpc, Governable
from ape_safe import ApeSafe

from scripts.access_control.bsc.access_control_eoa import all_governable_contracts
from scripts.utils import *

import time


def main():
    assert rpc.is_active(), "only fork rpc"

    # FIXME: fix exec address
    exec_safe = ApeSafe(SAFE_BSC_EXEC_ADDR)
    exec_account = exec_safe.account

    final_receipts = []

    for contract_addr in all_governable_contracts:
        contract = Governable.at(contract_addr)
        receipt = contract.acceptGovernor({"from": exec_account})
        final_receipts.append(receipt)

    # if submit safe transaction, skip running tests
    is_submit = yes_no_question("do we submit tx to safe wallet?", default=False)
    if is_submit:
        for i in range(0, len(final_receipts), 10):
            safe_tx = exec_safe.multisend_from_receipts(
                receipts=final_receipts[i : i + 10]
            )
            exec_safe.post_transaction(safe_tx)

        time.sleep(1)
        exit()

    # testing
    for contract_addr in all_governable_contracts:
        contract = Governable.at(contract_addr)
        assert contract.governor() == exec_account

    print("Done!")
