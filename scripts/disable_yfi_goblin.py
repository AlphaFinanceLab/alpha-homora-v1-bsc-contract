from brownie import accounts, interface, Contract
from brownie import (
    PancakeswapGoblinConfig, Bank, ConfigurableInterestBankConfig
)
from brownie import network
import eth_abi
from .utils import *

network.gas_price('5 gwei')


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

    configs = ['0x0000000000000000000000000000000000000000'] * len(goblin_v2_list)
    bank_config.setGoblins(goblin_v2_list, configs, {'from': deployer})
    
    print("Done!!!")
    print("End of deploy process!!!")

    ###########################################################
    # test banks with uniswap spell
    print('==========================================')
    print('start testing')


    alice = accounts[0]
    print('execute allbnb strategies; expect all error')
    bank = Bank.at('0x3bB5f6285c312fc7E1877244103036ebBEda193d')
    all_bnb_strategy_addr = '0x27d7dc4bfb0239376b7a597d130dd66eec97137f'
    BYFI = '0x88f1A5ae2A3BF98AEAF342D26B30a79438c9142e'
    for goblin_addr in goblin_v2_list:
        print('check', goblin_addr)
        try:
            bank.work(
                0,
                goblin_addr,
                0,
                0,
                eth_abi.encode_abi(
                    ['address', 'bytes'],
                    [
                        all_bnb_strategy_addr,
                        eth_abi.encode_abi(['address', 'uint'], [BYFI, 0])
                    ]
                ), 
                {'from': alice, 'value': '1 ether'}
            )
            assert False, 'the above command should be reverted'
        except Exception as err:
            print('got error as expect!!!')
            assert "not a goblin" in str(err), (
                f'incorrect msg error; got {err}'
            )
    
    
