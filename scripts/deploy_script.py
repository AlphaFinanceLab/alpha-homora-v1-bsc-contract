from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapPool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from brownie import network
from .utils import *
from .constant import *
import eth_abi

# set default gas price
network.gas_price('10 gwei')


def deploy(deployer):
    triple_slope_model = TripleSlopeModel.deploy({'from': deployer})

    # min debt 0.2 BNB at 10 gwei gas price (killBps 5% -> at least 0.01BNB bonus)
    # reserve pool bps 1000 (10%)
    # kill bps 500 (5%)
    bank_config = ConfigurableInterestBankConfig.deploy(
        2 * 10**17, 1000, 500, triple_slope_model, {'from': deployer})

    proxy_admin = ProxyAdminImpl.deploy({'from': deployer})
    bank_impl = Bank.deploy({'from': deployer})
    bank = TransparentUpgradeableProxyImpl.deploy(
        bank_impl, proxy_admin, bank_impl.initialize.encode_input(bank_config), {'from': deployer})
    bank = interface.IAny(bank)

    oracle = SimplePriceOracle.deploy({'from': deployer})

    # strats
    add_strat = StrategyAllBNBOnly.deploy(router_address, {'from': deployer})
    liq_strat = StrategyLiquidate.deploy(router_address, {'from': deployer})
    rem_strat = StrategyWithdrawMinimizeTrading.deploy(router_address, {'from': deployer})

    goblin_config = PancakeswapGoblinConfig.deploy(oracle, {'from': deployer})

    print('bank', bank.address)
    print('bank_config', bank_config.address)
    print('all bnb', add_strat.address)
    print('liq', liq_strat.address)
    print('withdraw', rem_strat.address)

    return bank, add_strat, liq_strat, rem_strat, bank_config, goblin_config, oracle


def deploy_pools(deployer, bank, add_strat, liq_strat, rem_strat, bank_config, goblin_config, oracle, pools):
    wbnb = interface.IAny(wbnb_address)

    prices = []
    tokens0 = []
    tokens1 = []

    registry = {}

    for pool in pools:
        fToken = interface.IAny(pool['token'])

        if fToken.address < wbnb_address:
            tokens0.append(fToken)
            tokens1.append(wbnb)
            price = (10**18 * wbnb.balanceOf(pool['lp'])) // fToken.balanceOf(pool['lp'])
            prices.append(price)
        else:
            tokens0.append(wbnb)
            tokens1.append(fToken)
            price = (10**18 * fToken.balanceOf(pool['lp'])) // wbnb.balanceOf(pool['lp'])
            prices.append(price)

        if pool['pid'] == 1:
            goblin = PancakeswapPool1Goblin.deploy(
                bank, chef_address, router_address, add_strat, liq_strat, 300, {'from': deployer})
        else:
            goblin = PancakeswapGoblin.deploy(
                bank, chef_address, router_address, pool['pid'], add_strat, liq_strat, 300, {'from': deployer})
        goblin_config.setConfigs([goblin], [pool['goblinConfig']], {'from': deployer})
        add_strat_2 = StrategyAddTwoSidesOptimal.deploy(router_address, goblin, {'from': deployer})
        goblin.setStrategyOk([add_strat_2, rem_strat], True, {'from': deployer})
        bank_config.setGoblins([goblin], [goblin_config], {'from': deployer})

        registry[pool['name']] = {'goblin': goblin, 'two_side': add_strat_2}

    # set oracle prices
    oracle.setPrices(tokens0, tokens1, prices, {'from': deployer})

    return registry


def test_cake(bank, registry, add_strat):
    alice = accounts[1]

    prevBNBBal = alice.balance()

    bank.work(0, registry['cake']['goblin'], 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [cake_address, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'


def test_cake_2(bank, registry):
    alice = accounts[1]

    prevBNBBal = alice.balance()

    bank.work(0, registry['cake']['goblin'], 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              registry['cake']['two_side'].address, eth_abi.encode_abi(['address', 'uint256', 'uint256'], [cake_address, 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'


def test_busd(bank, registry, add_strat):
    alice = accounts[1]

    prevBNBBal = alice.balance()

    bank.work(0, registry['busd']['goblin'], 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              add_strat.address, eth_abi.encode_abi(['address', 'uint256'], [busd_address, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'


def test_busd_2(bank, registry):
    alice = accounts[1]

    prevBNBBal = alice.balance()

    bank.work(0, registry['busd']['goblin'], 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              registry['busd']['two_side'].address, eth_abi.encode_abi(['address', 'uint256', 'uint256'], [cake_address, 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'


def main():
    deployer = accounts[8]
    # deployer = accounts.at('0xB593d82d53e2c187dc49673709a6E9f806cdC835', force=True)
    # deployer = accounts.load('gh')

    # deploy bank
    bank, add_strat, liq_strat, rem_strat, bank_config, goblin_config, oracle = deploy(deployer)

    pools = [
        {
            'name': 'cake',
            'token': cake_address,
            'lp': cake_lp_address,
            'pid': 1,
            'goblinConfig': [True, 7250, 8000, 100000]
        },
        {
            'name': 'busd',
            'token': busd_address,
            'lp': busd_lp_address,
            'pid': 2,
            'goblinConfig': [True, 7250, 8000, 100000]
        }]

    # deploy pools
    registry = deploy_pools(deployer, bank, add_strat, liq_strat, rem_strat,
                            bank_config, goblin_config, oracle, pools)

    #########################################################################
    # test work

    # test_cake(bank, registry, add_strat)
    # test_busd(bank, registry, add_strat)
    # test_cake_2(bank, registry)
    # test_busd_2(bank, registry)
