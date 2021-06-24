from brownie import accounts, interface, Contract
from brownie import (
    PancakeswapGoblinConfig, Bank, ConfigurableInterestBankConfig, PancakeswapGoblin
)
from brownie import network
import eth_abi
from .utils import *

network.gas_price('5 gwei')
# from brownie.network.gas.strategies import GasNowScalingStrategy
# gas_strategy = GasNowScalingStrategy(
#     initial_speed="fast", max_speed="fast", increment=1.085, block_duration=20)

# # set gas strategy
# network.gas_price(gas_strategy)


def main():
    deployer = accounts.at('0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('ghb')

    bank_config = ConfigurableInterestBankConfig.at('0x70DF43522D3a7332310b233De763758adCa14961')

    goblin_v2_list = [
        '0x7E52d9DbAF0366aAeC36175d551b21762336eCdb',  # yfi-bnb v2
    ]

    # check if goblin is goblin, and pid < 251 (v1 pools)
    for goblin in goblin_v2_list:
        assert bank_config.isGoblin(goblin), f'{goblin} is not goblin'
        assert interface.IAny(goblin).pid() >= 251, 'goblin is v1 pools'

    print('done checking...')

    all_bnb_strat_addr = {
        '0x7E52d9DbAF0366aAeC36175d551b21762336eCdb': '0x27d7dc4bfb0239376b7a597d130dd66eec97137f',
    }

    add_two_side_opt_strat_addr = {
        '0x7E52d9DbAF0366aAeC36175d551b21762336eCdb': '0x6ab62fc9a84850f2ff005704da7c32f3e5630dce',
    }

    goblins = {x: PancakeswapGoblin.at(x) for x in goblin_v2_list}

    for goblin_addr in goblin_v2_list:
        if goblin_addr in all_bnb_strat_addr:
            assert goblins[goblin_addr].okStrats(all_bnb_strat_addr[goblin_addr]) == True, (
                f'all-bnb strategy has already been disabled in {goblin_addr}'
            )
        if goblin_addr in add_two_side_opt_strat_addr:
            assert goblins[goblin_addr].okStrats(add_two_side_opt_strat_addr[goblin_addr]) == True, (
                f'add-two-side-opt strategy has already been disabled in {goblin_addr}'
            )

    print('disable allBNBOnly and addTwoSidesOptimal strategy')
    for goblin_addr, goblin in goblins.items():
        strategies = []
        if goblin_addr in all_bnb_strat_addr:
            strategies.append(all_bnb_strat_addr[goblin_addr])
        if goblin_addr in add_two_side_opt_strat_addr:
            strategies.append(add_two_side_opt_strat_addr[goblin_addr])
        goblin = PancakeswapGoblin.at(goblin_addr)
        goblin.setStrategyOk(strategies, False, {'from': deployer})

    print("Done!!!")
    print("End of deploy process!!!")

    # ###########################################################
    # # test banks with pancakeswap goblin
    # print('==========================================')
    # print('start testing')

    # alice = accounts[0]
    # print('execute allbnb strategies; expect all error')
    # bank = Bank.at('0x3bB5f6285c312fc7E1877244103036ebBEda193d')
    # tokens_for_goblin = {
    #     '0x7E52d9DbAF0366aAeC36175d551b21762336eCdb': BYFI,
    # }
    # for goblin_addr in goblin_v2_list:
    #     print('check', goblin_addr)
    #     try:
    #         bank.work(
    #             0,
    #             goblin_addr,
    #             0,
    #             0,
    #             eth_abi.encode_abi(
    #                 ['address', 'bytes'],
    #                 [
    #                     all_bnb_strat_addr[goblin_addr],
    #                     eth_abi.encode_abi(['address', 'uint'], [tokens_for_goblin[goblin_addr], 0])
    #                 ]
    #             ),
    #             {'from': alice, 'value': '1 ether'}
    #         )
    #         assert False, 'the above command should be reverted'
    #     except Exception as err:
    #         print('got error as expect!!!')
    #         assert "unapproved work strategy" in str(err), (
    #             f'incorrect msg error; got {err}'
    #         )

    # print('execute addTwoSidesOptimal strategy; expect error')
    # for goblin_addr in goblin_v2_list:
    #     print('check', goblin_addr)
    #     try:
    #         bank.work(
    #             0,
    #             goblin_addr,
    #             0,
    #             0,
    #             eth_abi.encode_abi(
    #                 ['address', 'bytes'],
    #                 [
    #                     add_two_side_opt_strat_addr[goblin_addr],
    #                     eth_abi.encode_abi(['address', 'uint', 'uint'], [tokens_for_goblin[goblin_addr], 0, 0])
    #                 ]
    #             ),
    #             {'from': alice, 'value': '1 ether'}
    #         )
    #         assert False, 'the above command should be reverted'
    #     except Exception as err:
    #         print('got error as expect!!!')
    #         assert "unapproved work strategy" in str(err), (
    #             f'incorrect msg error; got {err}'
    #         )

    # print('check reinvest')
    # for goblin_addr in goblin_v2_list:
    #     print('check', goblin_addr)
    #     tx = goblins[goblin_addr].reinvest({'from': alice})

    # print('End of testing!!!')
