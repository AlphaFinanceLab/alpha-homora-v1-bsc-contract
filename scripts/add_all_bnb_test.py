from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapPool1Goblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from .utils import *
import eth_abi


def main():
    admin = accounts[0]
    alice = accounts[1]
    bob = accounts[2]

    triple_slope_model = TripleSlopeModel.deploy({'from': admin})

    # min debt 0.2 BNB at 10 gwei gas price (killBps 5% -> at least 0.01BNB bonus)
    # reserve pool bps 1000 (10%)
    # kill bps 500 (5%)
    bank_config = ConfigurableInterestBankConfig.deploy(
        2 * 10**17, 1000, 500, triple_slope_model, {'from': admin})

    proxy_admin = ProxyAdminImpl.deploy({'from': admin})
    bank_impl = Bank.deploy({'from': admin})
    bank = TransparentUpgradeableProxyImpl.deploy(
        bank_impl, proxy_admin, bank_impl.initialize.encode_input(bank_config), {'from': admin})
    bank = interface.IAny(bank)

    cake = interface.IAny('0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82')
    wbnb = interface.IAny('0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c')
    chef = '0x73feaa1ee314f8c655e354234017be2193c9e24e'
    router = '0x05ff2b0db69458a0750badebc4f9e13add608c7f'  # pancake router

    oracle = SimplePriceOracle.deploy({'from': admin})
    oracle.setPrices([cake], [wbnb], [10**18 * 10 // 263], {'from': admin})

    # strats
    add_strat = StrategyAllBNBOnly.deploy(router, {'from': admin})
    liq_strat = StrategyLiquidate.deploy(router, {'from': admin})
    rem_strat = StrategyWithdrawMinimizeTrading.deploy(router, {'from': admin})

    # goblin
    goblin = PancakeswapPool1Goblin.deploy(
        bank, chef, router, add_strat, liq_strat, 300, {'from': admin})

    # new strat
    add_strat_2 = StrategyAddTwoSidesOptimal.deploy(router, goblin, cake, {'from': admin})
    goblin.setStrategyOk([add_strat_2], True, {'from': admin})

    # set whitelist cake
    add_strat.setWhitelistTokens([cake], [True], {'from': admin})
    liq_strat.setWhitelistTokens([cake], [True], {'from': admin})
    rem_strat.setWhitelistTokens([cake], [True], {'from': admin})

    # mint tokens
    mint_tokens(cake, alice)
    mint_tokens(wbnb, alice)

    # set goblin in bank config
    # work factor 72.5%
    # kill factor 80%
    # max price diff 1.1x (11000)
    goblin_config = PancakeswapGoblinConfig.deploy(oracle, {'from': admin})
    goblin_config.setConfigs([goblin], [[True, 6250, 7000, 11000]], {'from': admin})
    bank_config.setGoblins([goblin], [goblin_config], {'from': admin})

    bank.deposit({'from': bob, 'value': '1000 ether'})

    ############################################################################################
    print('==============')
    print('Case 0. set up initial borrow')
    alice = accounts[1]
    bob = accounts[2]

    bank.deposit({'from': bob, 'value': '2 ether'})

    prevBNBBal = alice.balance()

    bank.work(0, goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [add_strat_2.address,
                                                                              eth_abi.encode_abi(['address', 'uint256', 'uint256'], [cake.address, 0, 0])]), {'from': alice, 'value': '1 ether'})

    ###########################################################
    # work (no borrow)
    print('==============================================================')
    print('Case 1. work (no borrow)')

    deposit_amt = 10**18

    prevBNBBal = alice.balance()

    bank.work(0, goblin, 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [cake.address, 0])]), {'from': alice, 'value': deposit_amt})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(2))

    pos_health, pos_debt = bank.positionInfo(2)
    assert almostEqual(pos_health, 10 ** 18), 'position health should be ~1 BNB (swap fee 0.2%)'
    assert pos_debt == 0, 'position debt should be 0'

    ############################################################
    # work (borrow)
    print('==============================================================')
    print('Case 2. work 2x (borrow)')

    deposit_amt = 1 * 10**18
    borrow_amt = 1 * 10**18

    prevBNBBal = alice.balance()

    bank.work(0, goblin, borrow_amt, 0, eth_abi.encode_abi(['address', 'bytes'], [
              add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [cake.address, 0])]), {'from': alice, 'value': deposit_amt})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(3))

    pos_health, pos_debt = bank.positionInfo(3)
    assert almostEqual(curBNBBal - prevBNBBal, -deposit_amt), 'incorrect deposit amt'
    assert almostEqual(pos_debt, 1 * 10**18), 'debt != borrow amount'
    assert almostEqual(pos_health, deposit_amt +
                       borrow_amt), 'position health should be ~ deposited + borrow amt'
