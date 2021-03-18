from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapPool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from brownie import network
from .utils import *
from .constant import *
import eth_abi

# set default gas price
network.gas_price('10 gwei')


def test_token_1(bank, goblin, two_side, fToken):
    alice = accounts[1]
    bob = accounts[2]

    bank.deposit({'from': bob, 'value': '2 ether'})

    prevBNBBal = alice.balance()

    bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [fToken, 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)

    pos_id = bank.nextPositionID() - 1
    print('alice pos', bank.positionInfo(pos_id))


def test_token(bank, goblin, fToken, add_strat, liq_strat, rem_strat, add_strat_2):
    print('================================================')
    print('Testing')

    alice = accounts[1]
    bob = accounts[2]
    charlie = accounts[3]

    print('goblin', goblin)
    print('fToken', fToken)
    print('add_strat_2', add_strat_2)

    bank.deposit({'from': bob, 'value': '1 ether'})
    bank.deposit({'from': charlie, 'value': '1 ether'})

    prevBNBBal = alice.balance()

    bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [add_strat_2.address,
                                                                              eth_abi.encode_abi(['address', 'uint256', 'uint256'], [fToken, 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)

    pos_id = bank.nextPositionID() - 1
    print('alice pos', bank.positionInfo(pos_id))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'

    prevBNBBal = alice.balance()

    bank.work(pos_id, goblin, 0, 2**256-1, eth_abi.encode_abi(['address', 'bytes'], [
              liq_strat.address, eth_abi.encode_abi(['address', 'uint256'], [fToken, 0])]), {'from': alice})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(pos_id))

    if fToken == cake_address:
        bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [add_strat_2.address,
                                                                                  eth_abi.encode_abi(['address', 'uint256', 'uint256'], [fToken, 0, 0])]), {'from': alice, 'value': '1 ether'})
    else:
        bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [add_strat.address,
                                                                                  eth_abi.encode_abi(['address', 'uint256'], [fToken, 0])]), {'from': alice, 'value': '1 ether'})

    pos_id = bank.nextPositionID() - 1

    bank.work(pos_id, goblin, 0, 2**256-1, eth_abi.encode_abi(['address', 'bytes'], [
              rem_strat.address, eth_abi.encode_abi(['address', 'uint256'], [fToken, 0])]), {'from': alice})

    print('reinvesting')
    goblin.reinvest({'from': alice})

    print('liquidating')
    bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [add_strat_2.address,
                                                                              eth_abi.encode_abi(['address', 'uint256', 'uint256'], [fToken, 0, 0])]), {'from': alice, 'value': '1 ether'})

    pos_id = bank.nextPositionID() - 1

    pre_bank_bal = bank.balance()

    goblin.liquidate(pos_id, {'from': bank, 'gas_price': 0})

    post_bank_bal = bank.balance()

    print('liq gain', post_bank_bal - pre_bank_bal)
    assert post_bank_bal - pre_bank_bal > 0, 'liq gets 0'


def main():

    deployer = accounts.at('0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('ghb')

    triple_slope = TripleSlopeModel.at('0x9b0432c1800f35fd5235d24c2e223c45cefe0864')
    bank_config = ConfigurableInterestBankConfig.at('0x70df43522d3a7332310b233de763758adca14961')
    bank_impl = Bank.at('0x35cfacc93244fc94d26793cd6e68f59976380b3e')
    bank = Bank.at('0x3bb5f6285c312fc7e1877244103036ebbeda193d')
    add_strat = StrategyAllBNBOnly.at('0x06a34a95b3e1064295e93e9c92c15a4ebfed7eef')
    liq_strat = StrategyLiquidate.at('0x034c0d2b94a2b843c3cccae6be0f74f44b5dd3f9')
    rem_strat = StrategyWithdrawMinimizeTrading.at('0xbd1c05cbe5f7c625bb7877caa23ba461abae4887')
    goblin_config = PancakeswapGoblinConfig.at('0x8703f72dbdcd169a9c702e7044603ebbfb11425c')

    cake_goblin = PancakeswapPool1Goblin.at('0xaa00f2b7dd0de46c6fc9655dbadd80ac91a66869')
    busd_goblin = PancakeswapGoblin.at('0x08d871ddad70bd3aef3fecfbf4350debc57d8264')
    btc_goblin = PancakeswapGoblin.at('0x549ef362657a3e3923793a494db3d89e3e5fda35')
    eth_goblin = PancakeswapGoblin.at('0x2f050b64ede3b1d21184435974bb1d2fe02012b6')
    usdt_goblin = PancakeswapGoblin.at('0x3974071481dad49ac94ca1756f311c872ec3e26e')
    alpha_goblin = PancakeswapGoblin.at('0xa0aa119e0324d864831c24b78e85927526e42d52')

    band_goblin = PancakeswapGoblin.at('0xC3c16508E77E99e67CFCD30B765e48a5A33D4c9d')
    link_goblin = PancakeswapGoblin.at('0x047683a9A7958c02ca86B6eECea1f8ACfBd54f4F')
    yfi_goblin = PancakeswapGoblin.at('0x3663AeDeBB70DCF0A64e2600233D6913dD3eCf2B')
    uni_goblin = PancakeswapGoblin.at('0xfdCdF8D07db8C5B33fbF46f41Eced421d9d32bEE')

    # for new_goblin in new_goblin_list:
    #     assert new_goblin.addStrat() == busd_goblin.addStrat(), 'incorrect add strat'
    #     assert new_goblin.masterChef() == busd_goblin.masterChef(), 'incorrect masterchef'
    #     assert new_goblin.router() == busd_goblin.router(), 'incorrect router'
    #     assert new_goblin.addStrat() == busd_goblin.addStrat(), 'incorrect addStrat'
    #     assert new_goblin.liqStrat() == busd_goblin.liqStrat(), 'incorrect liqStrat'
    #     assert new_goblin.reinvestBountyBps() == 30, 'incorrect bounty bps'

    # assert band_goblin.pid() == 4, 'incorrect band pid'
    # assert link_goblin.pid() == 7, 'incorrect link pid'
    # assert yfi_goblin.pid() == 24, 'incorrect yfi pid'
    # assert uni_goblin.pid() == 25, 'incorrect uni pid'

    cake_two_side = StrategyAddTwoSidesOptimal.at('0x93db96377706693b0c4548efaddb73dce4a3f14b')
    busd_two_side = StrategyAddTwoSidesOptimal.at('0x1805f590c13ec9c59a197400f56b4b0d1adec796')
    btc_two_side = StrategyAddTwoSidesOptimal.at('0x8240600913c1a8b3d80b29245d94f2af09facac8')
    eth_two_side = StrategyAddTwoSidesOptimal.at('0x40bdfa199ef27143f0ce292a162450cf5512c390')
    usdt_two_side = StrategyAddTwoSidesOptimal.at('0x7fcae7fd3cb010c30751420a2553bc8232923eae')
    alpha_two_side = StrategyAddTwoSidesOptimal.at('0xb8bd068dd234d9cc06763cfbcea53ecd60e82b8d')

    band_two_side = StrategyAddTwoSidesOptimal.at('0xDDa8648FbFeD2f2AbD0dFCa404c7D8F154ccB8b7')
    link_two_side = StrategyAddTwoSidesOptimal.at('0xBD6600922422FD84f02b47B40cD83a4F25D1B12D')
    yfi_two_side = StrategyAddTwoSidesOptimal.at('0x44A819A0d93849bd6587cD6000e91Bf8b302Deaa')
    uni_two_side = StrategyAddTwoSidesOptimal.at('0x397f4605B953134f2Cf5f1176A25a7f5171C2925')

    new_two_sides = [band_two_side, link_two_side, yfi_two_side, uni_two_side]
    fToken_list = [band_address, link_address, yfi_address, uni_address]

    # for i in range(4):
    #     new_goblin = new_goblin_list[i]
    #     new_two_side = new_two_sides[i]

    #     assert new_two_side.router() == cake_two_side.router(), 'incorrect router'
    #     assert new_two_side.goblin(
    #     ) == new_goblin, f'incorrect goblin {new_two_side.goblin()}, {new_goblin}'
    #     assert new_two_side.fToken_() == new_goblin.fToken(), 'incorrect fToken'
    #     assert new_two_side.fToken_() == fToken_list[i], 'incorrect fToken'

    ##############################################################
    # deploy new pools

    new_goblin_list = [band_goblin, link_goblin, yfi_goblin, uni_goblin]
    new_two_sides = [band_two_side, link_two_side, yfi_two_side, uni_two_side]
    fToken_list = [band_address, link_address, yfi_address, uni_address]
    configs = [
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000]
    ]

    deploy_indices = [0, 1, 2, 3]
    deploy_goblins = [new_goblin_list[i] for i in deploy_indices]
    deploy_two_sides = [new_two_sides[i] for i in deploy_indices]
    deploy_fTokens = [fToken_list[i] for i in deploy_indices]
    deploy_configs = [configs[i] for i in deploy_indices]

    # set goblin config
    bank_config.setGoblins(deploy_goblins, [goblin_config]
                           * len(deploy_goblins), {'from': deployer})

    # set configs
    goblin_config.setConfigs(deploy_goblins, deploy_configs, {'from': deployer})

    # set strat ok to two_side adn rem_strat
    assert len(deploy_goblins) == len(deploy_two_sides), 'length mismatched'

    for i in range(len(deploy_goblins)):
        goblin = deploy_goblins[i]
        add_strat_2 = deploy_two_sides[i]

        goblin.setStrategyOk([add_strat_2, rem_strat], True, {'from': deployer})

    add_strat.setWhitelistTokens(deploy_fTokens, [True] * len(deploy_fTokens), {'from': deployer})
    liq_strat.setWhitelistTokens(deploy_fTokens, [True] * len(deploy_fTokens), {'from': deployer})
    rem_strat.setWhitelistTokens(deploy_fTokens, [True] * len(deploy_fTokens), {'from': deployer})

    ##############################################################
    # test work

    # make sure remaining debt is not too small
    # test_token_1(bank, cake_goblin, cake_two_side, cake_address)

    # for i in range(len(deploy_goblins)):
    #     goblin = deploy_goblins[i]
    #     add_strat_2 = deploy_two_sides[i]
    #     fToken = deploy_fTokens[i]

    #     test_token(bank, goblin, fToken, add_strat, liq_strat, rem_strat, add_strat_2)
