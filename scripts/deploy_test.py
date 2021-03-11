from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapPool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from .utils import *
import eth_abi
from .constant import *


def deploy_goblin(admin, pools, bank_config, bank, oracle, add_strat, liq_strat, rem_strat, goblin_config):
    wbnb = interface.IAny(wbnb_address)

    res = []
    for pool in pools:
        fToken = interface.IAny(pool["token"])

        if fToken.address < wbnb_address:
            price = (10**18 * wbnb.balanceOf(pool['lp'])) // fToken.balanceOf(pool['lp'])
            oracle.setPrices([fToken], [wbnb], [price], {'from': admin})
        else:
            price = (10**18 * fToken.balanceOf(pool['lp'])) // wbnb.balanceOf(pool['lp'])
            oracle.setPrices([wbnb], [fToken], [price], {'from': admin})

        if pool['pid'] == 1:
            goblin = PancakeswapPool1Goblin.deploy(
                bank, chef_address, router_address, add_strat, liq_strat, 300, {'from': admin})
        else:
            goblin = PancakeswapGoblin.deploy(
                bank, chef_address, router_address, pool['pid'], add_strat, liq_strat, 300, {'from': admin})
        goblin_config.setConfigs([goblin], [pool["goblinConfig"]], {'from': admin})
        add_strat_2 = StrategyAddTwoSidesOptimal.deploy(router_address, goblin, {'from': admin})
        goblin.setStrategyOk([add_strat_2, rem_strat], True, {'from': admin})
        bank_config.setGoblins([goblin], [goblin_config], {'from': admin})

        res.append({
            "pool": pool,
            "goblin": goblin,
            "twoSide": add_strat_2
        })
    return res


def deploy(admin, pools):
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

    oracle = SimplePriceOracle.deploy({'from': admin})

    # strats
    add_strat = StrategyAllBNBOnly.deploy(router_address, {'from': admin})
    liq_strat = StrategyLiquidate.deploy(router_address, {'from': admin})
    rem_strat = StrategyWithdrawMinimizeTrading.deploy(router_address, {'from': admin})

    goblin_config = PancakeswapGoblinConfig.deploy(oracle, {'from': admin})

    results = deploy_goblin(admin, pools, bank_config, bank, oracle,
                            add_strat, liq_strat, rem_strat, goblin_config)

    print('bank', bank.address)
    print('bank_config', bank_config.address)
    print('all bnb', add_strat.address)
    print('liq', liq_strat.address)
    print('withdraw', rem_strat.address)

    for res in results:
        print(res['pool']['name'], res['goblin'].address, res['twoSide'].address)

    return bank, add_strat, liq_strat, rem_strat, results


def main():
    admin = accounts[0]
    alice = accounts[1]

    deployed_pools = list(filter(lambda pool: pool['name'] == 'cake', pools))
    bank, add_strat, liq_strat, rem_strat, results = deploy(admin, deployed_pools)

    bank.deposit({
        "from": admin,
        "value": '100 ether'
    })

    wbnb = interface.IAny(wbnb_address)
    cake = interface.IAny(cake_address)
    cake_goblin = next((res["goblin"]
                        for res in results if res["pool"]["token"] == cake_address), None)

    # mint tokens
    mint_tokens(cake, alice)
    mint_tokens(wbnb, alice)

    # approve tokens
    cake.approve(bank, 2**256-1, {'from': alice})
    wbnb.approve(bank, 2**256-1, {'from': alice})

    ###########################################################
    # work
    prevBNBBal = alice.balance()

    bank.work(0, cake_goblin, 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [cake.address, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    pass
