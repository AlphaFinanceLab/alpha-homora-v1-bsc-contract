from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapPool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from brownie import network
from .utils import *
from .constant import *
import eth_abi

# set default gas price
network.gas_price('5 gwei')


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
    # deployer = accounts[8]
    deployer = accounts.at('0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('')

    # deploy bank
    # bank, add_strat, liq_strat, rem_strat, bank_config, goblin_config, oracle = deploy(deployer)

    triple_slope = TripleSlopeModel.at('0x9b0432c1800f35fd5235d24c2e223c45cefe0864')
    bank_config = ConfigurableInterestBankConfig.at('0x70df43522d3a7332310b233de763758adca14961')
    bank_impl = Bank.at('0x35cfacc93244fc94d26793cd6e68f59976380b3e')
    bank = Bank.at('0x3bb5f6285c312fc7e1877244103036ebbeda193d')
    add_strat = StrategyAllBNBOnly.at('0x06a34a95b3e1064295e93e9c92c15a4ebfed7eef')
    liq_strat = StrategyLiquidate.at('0x034c0d2b94a2b843c3cccae6be0f74f44b5dd3f9')
    rem_strat = StrategyWithdrawMinimizeTrading.at('0xbd1c05cbe5f7c625bb7877caa23ba461abae4887')
    goblin_config = PancakeswapGoblinConfig.at('0x8703f72dbdcd169a9c702e7044603ebbfb11425c')
    oracle = SimplePriceOracle.at('0xc0d0a48f8feec21b60cf8ba2a372199ebf3b740a')

    pools = [
        {
            "name": "front",
            "token": front_address,
            "lp": front_lp_address,
            "pid": 57,
            "goblinConfig": [True, 5250, 6000, 11000]
        },
        {
            "name": "dot",
            "token": dot_address,
            "lp": dot_lp_address,
            "pid": 5,
            "goblinConfig": [True, 6250, 7000, 11000]
        },
        {
            "name": "xvs",
            "token": xvs_address,
            "lp": xvs_lp_address,
            "pid": 13,
            "goblinConfig": [True, 5250, 6000, 11000]
        },
        {
            "name": "inj",
            "token": inj_address,
            "lp": inj_lp_address,
            "pid": 27,
            "goblinConfig": [True, 6250, 7000, 11000]
        }]

    # deploy pools
    registry = deploy_pools(deployer, bank, add_strat, liq_strat, rem_strat,
                            bank_config, goblin_config, oracle, pools)

    # set whitelist tokens to add_strat
    add_fTokens = list(map(lambda pool: pool['token'], pools))
    add_strat.setWhitelistTokens(add_fTokens, [True] * len(add_fTokens), {'from': deployer})

    # set whitelist tokens to liq_strat, rem_strat
    fTokens = list(map(lambda pool: pool['token'], pools))
    liq_strat.setWhitelistTokens(fTokens, [True] * len(fTokens), {'from': deployer})
    rem_strat.setWhitelistTokens(fTokens, [True] * len(fTokens), {'from': deployer})

    #########################################################################
    # test work

    # test_token(bank, registry, add_strat, liq_strat, rem_strat, 'front')
    # test_token(bank, registry, add_strat, liq_strat, rem_strat, 'dot')
    # test_token(bank, registry, add_strat, liq_strat, rem_strat, 'xvs')
    # test_token(bank, registry, add_strat, liq_strat, rem_strat, 'inj')
