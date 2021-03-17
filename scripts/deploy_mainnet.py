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

    # min debt 1 BNB at 10 gwei gas price (avg gas fee = ~0.006 BNB) (killBps 1% -> at least 0.01BNB bonus)
    # reserve pool bps 2000 (20%)
    # kill bps 100 (1%)
    bank_config = ConfigurableInterestBankConfig.deploy(
        10**18, 2000, 100, triple_slope_model, {'from': deployer})

    proxy_admin = ProxyAdminImpl.deploy({'from': deployer})
    bank_impl = Bank.deploy({'from': deployer})
    bank = TransparentUpgradeableProxyImpl.deploy(
        bank_impl, proxy_admin, bank_impl.initialize.encode_input(bank_config), {'from': deployer})
    bank = interface.IAny(bank)

    # oracle = SimplePriceOracle.deploy({'from': deployer})
    oracle = SimplePriceOracle.at('0xc0d0A48F8Feec21B60Cf8BA2A372199ebf3B740a')

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

    registry = {}

    for pool in pools:
        print('==============================')
        print('deploying pool', pool['name'])
        fToken = interface.IAny(pool['token'])

        if pool['pid'] == 1:
            # reinvest 0.3% (avg gas fee ~0.006 BNB)
            goblin = PancakeswapPool1Goblin.deploy(
                bank, chef_address, router_address, add_strat, liq_strat, 30, {'from': deployer})
        else:
            # reinvest 0.3% (avg gas fee ~0.006 BNB)
            goblin = PancakeswapGoblin.deploy(
                bank, chef_address, router_address, pool['pid'], add_strat, liq_strat, 30, {'from': deployer})
        goblin_config.setConfigs([goblin], [pool['goblinConfig']], {'from': deployer})
        add_strat_2 = StrategyAddTwoSidesOptimal.deploy(
            router_address, goblin, fToken, {'from': deployer})
        goblin.setStrategyOk([add_strat_2, rem_strat], True, {'from': deployer})
        bank_config.setGoblins([goblin], [goblin_config], {'from': deployer})

        # re-assign two side strat as add strat for pool 1 goblin
        if pool['pid'] == 1:
            goblin.setCriticalStrategies(add_strat_2, liq_strat, {'from': deployer})
            goblin.setStrategyOk([add_strat], False, {'from': deployer})  # unset add_strat

        registry[pool['name']] = {'goblin': goblin,
                                  'two_side': add_strat_2, 'token': fToken.address}

    return registry


def test_cake_2(bank, registry):
    alice = accounts[1]

    prevBNBBal = alice.balance()

    bank.work(0, registry['cake']['goblin'], 0, 0, eth_abi.encode_abi(['address', 'bytes'], [
              registry['cake']['two_side'].address, eth_abi.encode_abi(['address', 'uint256', 'uint256'], [cake_address, 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)
    print('alice pos', bank.positionInfo(1))

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect BNB input amount'

    # test reinvest
    chain.mine(10)

    goblin = interface.IAny(registry['cake']['goblin'])
    goblin.reinvest({'from': alice})


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


def test_token_1(bank, registry, token_name):
    alice = accounts[1]
    bob = accounts[2]

    bank.deposit({'from': bob, 'value': '2 ether'})

    prevBNBBal = alice.balance()

    bank.work(0, registry[token_name]['goblin'], 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [registry[token_name]['two_side'].address,
                                                                                                      eth_abi.encode_abi(['address', 'uint256', 'uint256'], [registry[token_name]['token'], 0, 0])]), {'from': alice, 'value': '1 ether'})

    curBNBBal = alice.balance()

    print('∆ bnb alice', curBNBBal - prevBNBBal)

    pos_id = bank.nextPositionID() - 1
    print('alice pos', bank.positionInfo(pos_id))


def test_token(bank, registry, add_strat, liq_strat, rem_strat, token_name):
    print('================================================')
    print('Testing', token_name)

    alice = accounts[1]
    bob = accounts[2]

    goblin = registry[token_name]['goblin']
    fToken = registry[token_name]['token']
    add_strat_2 = registry[token_name]['two_side']

    print('goblin', goblin)
    print('fToken', fToken)
    print('add_strat_2', add_strat_2)

    bank.deposit({'from': bob, 'value': '2 ether'})

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

    if token_name == 'cake':
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
    deployer = accounts[8]
    # deployer = accounts.at('0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('')

    # deploy bank
    bank, add_strat, liq_strat, rem_strat, bank_config, goblin_config, oracle = deploy(deployer)

    pools = [
        {
            'name': 'cake',
            'token': cake_address,
            'lp': cake_lp_address,
            'pid': 1,
            'goblinConfig': [True, 6250, 7000, 11000]
        },
        {
            'name': 'busd',
            'token': busd_address,
            'lp': busd_lp_address,
            'pid': 2,
            'goblinConfig': [True, 7000, 8000, 11000]
        },
        {
            "name": "btcb",
            "token": btcb_address,
            "lp": btcb_lp_address,
            "pid": 15,
            "goblinConfig": [True, 7000, 8000, 11000]
        },
        {
            "name": "eth",
            "token": eth_address,
            "lp": eth_lp_address,
            "pid": 14,
            "goblinConfig": [True, 7000, 8000, 11000]
        },
        {
            "name": "usdt",
            "token": usdt_address,
            "lp": usdt_lp_address,
            "pid": 17,
            "goblinConfig": [True, 7000, 8000, 11000]
        },
        {
            "name": "alpha",
            "token": alpha_address,
            "lp": alpha_lp_address,
            "pid": 16,
            "goblinConfig": [True, 6250, 7000, 11000]
        }]

    # deploy pools
    registry = deploy_pools(deployer, bank, add_strat, liq_strat, rem_strat,
                            bank_config, goblin_config, oracle, pools)

    # set whitelist tokens to add_strat (no CAKE)
    add_fTokens = list(map(lambda pool: pool['token'], pools[1:]))
    add_strat.setWhitelistTokens(add_fTokens, [True] * len(add_fTokens), {'from': deployer})

    # set whitelist tokens to liq_strat, rem_strat
    fTokens = list(map(lambda pool: pool['token'], pools))
    liq_strat.setWhitelistTokens(fTokens, [True] * len(fTokens), {'from': deployer})
    rem_strat.setWhitelistTokens(fTokens, [True] * len(fTokens), {'from': deployer})

    #########################################################################
    # test work

    # test_busd(bank, registry, add_strat)
    # test_cake_2(bank, registry)
    # test_busd_2(bank, registry)

    test_token_1(bank, registry, 'cake')  # make sure remaining debt is not too small
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'cake')
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'busd')
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'btcb')
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'eth')
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'alpha')
    test_token(bank, registry, add_strat, liq_strat, rem_strat, 'usdt')
