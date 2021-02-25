from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig)
from .utils import *
import eth_abi
from .constant import *

def deploy(bank_config, bank, oracle, add_strat, liq_strat, rem_strat, goblin_config):
    wbnb = interface.IAny(wbnb_address)

    res = []
    for pool in pools:
        fToken = interface.IAny(pool["token"])
        price = (10**18 * wbnb.balanceOf(pool["lp"])) // cake.balanceOf(pool["lp"])
        oracle.setPrices([fToken], [wbnb], [price], {'from': admin})
        goblin = PancakeswapGoblin.deploy(
            bank, chef_address, router_address, pool["pid"], add_strat, liq_strat, 300, {'from': admin})
        goblin_config.setConfigs([goblin], [pool["goblinConfig"]], {'from': admin})
        bank_config.setGoblins([goblin], [goblin_config], {'from': admin})
        res.append({
            "pool": pool,
            "goblin": goblin,
        })


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

    oracle = SimplePriceOracle.deploy({'from': admin})
    
    # strats
    add_strat = StrategyAllBNBOnly.deploy(router_address, {'from': admin})
    liq_strat = StrategyLiquidate.deploy(router_address, {'from': admin})
    rem_strat = StrategyWithdrawMinimizeTrading.deploy(router_address, {'from': admin})

    # new strat
    add_strat_2 = StrategyAddTwoSidesOptimal.deploy(router_address, goblin, {'from': admin})
    goblin.setStrategyOk([add_strat_2], True, {'from': admin})

    # set goblin in bank config
    # work factor 72.5%
    # kill factor 80%
    # max price diff 10%
    goblin_config = PancakeswapGoblinConfig.deploy(oracle, {'from': admin})
    
    deploy(bank_config, bank, oracle, add_strat, liq_strat, rem_strat, goblin_config)

    bank.deposit({
        "from": admin,
        "value": '100 ether'
    })

    # mint tokens
    mint_tokens(cake, alice)
    mint_tokens(wbnb, alice)

    # approve tokens
    cake.approve(bank, 2**256-1, {'from': alice})
    wbnb.approve(bank, 2**256-1, {'from': alice})

    ###########################################################
    # work

    # prevBNBBal = alice.balance()

    # bank.work(0, goblin, 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
    #           add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [cake.address, 0])]), {'from': alice, 'value': '1 ether'})

    # curBNBBal = alice.balance()

    # print('∆ bnb alice', curBNBBal - prevBNBBal)
    # print('alice pos', bank.positionInfo(1))

    # pass
