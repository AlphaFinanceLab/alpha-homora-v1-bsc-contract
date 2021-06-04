from scripts.deploy_mainnet import deploy
from brownie import accounts, interface, Contract
from brownie import (
    PancakeswapGoblinConfig, Bank, ConfigurableInterestBankConfig, PancakeswapGoblin,
    StrategyAddTwoSidesOptimal, StrategyAllBNBOnly
)
from brownie import network
from .utils import *
import eth_abi

network.gas_price('5 gwei')

# from brownie.network.gas.strategies import GasNowScalingStrategy
# gas_strategy = GasNowScalingStrategy(
#     initial_speed="fast", max_speed="fast", increment=1.085, block_duration=20)

# # set gas strategy
# network.gas_price(gas_strategy)

def main():
    deployer = accounts.at(
        '0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('ghb')

    goblin_pancake_v1_list = [
        # This one is pancake goblin pool1 but can use PancakeswapGoblin as an interface
        '0xAA00F2b7Dd0De46C6FC9655DBADD80AC91a66869',  # cake -
        # Belows are pancake goblin.
        '0x08D871dDAD70bD3aef3fecfBf4350debc57d8264',  # busd -
        '0x549eF362657a3E3923793A494db3D89E3e5Fda35',  # btc -
        '0x2f050B64Ede3b1D21184435974bB1d2fe02012B6',  # eth -
        '0x3974071481daD49AC94Ca1756F311C872eC3e26e',  # usdt -
        '0xfdCdF8D07db8C5B33fbF46f41Eced421d9d32bEE',  # uni -
        '0x047683a9A7958c02ca86B6eECea1f8ACfBd54f4F',  # link -
        '0xC3c16508E77E99e67CFCD30B765e48a5A33D4c9d',  # band -
        '0x3663AeDeBB70DCF0A64e2600233D6913dD3eCf2B',  # yfi -
        '0xa0aA119e0324d864831c24B78e85927526e42D52',  # alpha -
        '0x62e32E6eBEabf776B59F5Dfb9B364779C3a64137',  # inj -
        '0x567f4a45d45945a75898be4cad299a8f32c86d08',  # dot -
        '0xD6D8f5E06f655Ff01Bb3b08DD65946BabbFEc351',  # xvs -
        '0x3Cab9D2Ca781C6b6cF8D29bFb450aa4fFFCae854',  # front -
    ]

    allbnb_strategy = StrategyAllBNBOnly.at('0x06A34A95b3e1064295e93E9C92c15A4eBFeD7eEf')
    add_two_side_strategy = StrategyAddTwoSidesOptimal.at('0xe15e4a5c2b6ea78cc12e7d320b732924b64e6137')

    print('disable allBNBOnly and addTwoSidesOptimal strategy')
    for goblin_addr in goblin_pancake_v1_list:
        goblin = PancakeswapGoblin.at(goblin_addr)
        goblin.setStrategyOk(
            [allbnb_strategy, add_two_side_strategy],
            False,
            {'from': deployer}
        )

    print("Done!!!")
    print("End of deploy process!!!")

    ###########################################################
    # test banks with uniswap spell
    print('==========================================')
    print('start testing')


    alice = accounts[0]
    bank = Bank.at('0x3bB5f6285c312fc7E1877244103036ebBEda193d')
    for goblin_addr in goblin_pancake_v1_list:
        
        print('execute allbnb strategy; expect error')
        try:
            bank.work(
                0,
                goblin_addr,
                0,
                0,
                eth_abi.encode_abi(
                    ['address', 'bytes'],
                    [
                        allbnb_strategy.address,
                        eth_abi.encode_abi(['address', 'uint'], [CAKE, 0])
                    ]
                ), 
                {'from': alice, 'value': '1 ether'}
            )
            assert False, 'the above command should be reverted'
        except Exception as err:
            print('got error as expect!!!')
            assert "unapproved work strategy" in str(err), (
                f'incorrect msg error; got {err}'
            )

        print('execute addTwoSidesOptimal strategy; expect error')
        try:
            bank.work(
                0,
                goblin_addr,
                0,
                0,
                eth_abi.encode_abi(
                    ['address', 'bytes'],
                    [
                        add_two_side_strategy.address,
                        eth_abi.encode_abi(['address', 'uint', 'uint'], [CAKE, 0, 0])
                    ]
                ), 
                {'from': alice, 'value': '1 ether'}
            )
            assert False, 'the above command should be reverted'
        except Exception as err:
            print('got error as expect!!!')
            assert "unapproved work strategy" in str(err), (
                f'incorrect msg error; got {err}'
            )

