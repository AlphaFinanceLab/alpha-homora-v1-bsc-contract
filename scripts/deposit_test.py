from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapPool1Goblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig)
from .utils import *
import eth_abi


def main():
    admin = accounts[0]
    alice = accounts[1]

    triple_slope_model = TripleSlopeModel.deploy({'from': admin})

    # min debt 0.2 BNB at 10 gwei gas price (killBps 5% -> at least 0.01BNB bonus)
    # reserve pool bps 1000 (10%)
    # kill bps 500 (5%)
    bank_config = ConfigurableInterestBankConfig.deploy(
        2 * 10**17, 1000, 500, triple_slope_model, {'from': admin})
    bank = Bank.deploy(bank_config, {'from': admin})

    ###################################################################
    # deposit & withdraw

    deposit_amt = 10**18

    prevBNBBal = alice.balance()
    prevIbBNBBal = bank.balanceOf(alice)

    bank.deposit({'from': alice, 'value': deposit_amt})

    curBNBBal = alice.balance()
    curIbBNBBal = bank.balanceOf(alice)

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('∆ ibBNB alice', curIbBNBBal - prevIbBNBBal)

    assert curBNBBal - prevBNBBal == -(curIbBNBBal - prevIbBNBBal), 'first depositor should get 1:1'
    assert curBNBBal - prevBNBBal == -deposit_amt

    # withdraw 1/3
    prevBNBBal = alice.balance()
    prevIbBNBBal = bank.balanceOf(alice)

    bank.withdraw(curIbBNBBal // 3, {'from': alice})

    curBNBBal = alice.balance()
    curIbBNBBal = bank.balanceOf(alice)

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('∆ ibBNB alice', curIbBNBBal - prevIbBNBBal)

    assert curBNBBal - prevBNBBal == -(curIbBNBBal - prevIbBNBBal), 'first depositor should get 1:1'
    assert curBNBBal - prevBNBBal == deposit_amt // 3

    # withdraw remaining
    prevBNBBal = alice.balance()
    prevIbBNBBal = bank.balanceOf(alice)

    bank.withdraw(curIbBNBBal, {'from': alice})

    curBNBBal = alice.balance()
    curIbBNBBal = bank.balanceOf(alice)

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('∆ ibBNB alice', curIbBNBBal - prevIbBNBBal)

    assert curBNBBal - prevBNBBal == -(curIbBNBBal - prevIbBNBBal), 'first depositor should get 1:1'
    assert curBNBBal - prevBNBBal == deposit_amt - deposit_amt // 3
