from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapV2Goblin,
                     StrategyAllBNBOnlyV2, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimalV2, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapV2Pool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from brownie import network
from .utils import *
from .constant import *
import eth_abi

# set default gas price
network.gas_price('5 gwei')


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
    add_strat = StrategyAllBNBOnlyV2.at('')  # TODO: wait for deploy
    liq_strat = StrategyLiquidate.at('')  # TODO: wait for deploy
    rem_strat = StrategyWithdrawMinimizeTrading.at('')  # TODO: wait for deploy
    goblin_config = PancakeswapGoblinConfig.at('0x8703f72dbdcd169a9c702e7044603ebbfb11425c')

    cake_goblin = PancakeswapV2Pool1Goblin.at('')
    busd_goblin = PancakeswapV2Goblin.at('')
    btc_goblin = PancakeswapV2Goblin.at('')
    eth_goblin = PancakeswapV2Goblin.at('')
    usdt_goblin = PancakeswapV2Goblin.at('')
    alpha_goblin = PancakeswapV2Goblin.at('')
    uni_goblin = PancakeswapV2Goblin.at('')
    link_goblin = PancakeswapV2Goblin.at('')
    band_goblin = PancakeswapV2Goblin.at('')
    yfi_goblin = PancakeswapV2Goblin.at('')
    front_goblin = PancakeswapV2Goblin.at('')
    dot_goblin = PancakeswapV2Goblin.at('')
    xvs_goblin = PancakeswapV2Goblin.at('')
    inj_goblin = PancakeswapV2Goblin.at('')

    new_goblin_list = [
        cake_goblin,
        busd_goblin,
        btc_goblin,
        eth_goblin,
        usdt_goblin,
        alpha_goblin,
        uni_goblin,
        link_goblin,
        band_goblin,
        yfi_goblin,
        front_goblin,
        dot_goblin,
        xvs_goblin,
        inj_goblin
    ]

    new_two_sides = [
        cake_two_side,
        busd_two_side,
        btc_two_side,
        eth_two_side,
        usdt_two_side,
        alpha_two_side,
        uni_two_side,
        link_two_side,
        band_two_side,
        yfi_two_side,
        front_two_side,
        dot_two_side,
        xvs_two_side,
        inj_two_side
    ]

    fToken_list = [
        cake_address,
        busd_address,
        btcb_address,
        eth_address,
        usdt_address,
        alpha_address,
        uni_address,
        link_address,
        band_address,
        yfi_address,
        front_address,
        dot_address,
        xvs_address,
        inj_address
    ]

    print('done loading goblins')

    for new_goblin in new_goblin_list:
        if new_goblin != cake_goblin:
            assert new_goblin.addStrat() == busd_goblin.addStrat(), 'incorrect add strat'
        assert new_goblin.masterChef() == busd_goblin.masterChef(), 'incorrect masterchef'
        assert new_goblin.router() == busd_goblin.router(), 'incorrect router'
        assert new_goblin.liqStrat() == busd_goblin.liqStrat(), 'incorrect liqStrat'
        assert new_goblin.reinvestBountyBps() == 30, 'incorrect bounty bps'

    assert cake_goblin.pid() == 139, 'incorrect cake pid'
    assert busd_goblin.pid() == 140, 'incorrect busd pid'
    assert btc_goblin.pid() == 150, 'incorrect btc pid'
    assert eth_goblin.pid() == 149, 'incorrect eth pid'
    assert usdt_goblin.pid() == 152, 'incorrect usdt pid'
    assert alpha_goblin.pid() == 151, 'incorrect alpha pid'
    assert uni_goblin.pid() == 157, 'incorrect uni pid'
    assert link_goblin.pid() == 145, 'incorrect link pid'
    assert band_goblin.pid() == 142, 'incorrect band pid'
    assert yfi_goblin.pid() == 156, 'incorrect yfi pid'
    assert front_goblin.pid() == 176, 'incorrect front pid'
    assert dot_goblin.pid() == 143, 'incorrect dot pid'
    assert xvs_goblin.pid() == 148, 'incorrect xvs pid'
    assert inj_goblin.pid() == 159, 'incorrect uni pid'

    print('done asserting goblins')

    cake_two_side = StrategyAddTwoSidesOptimalV2.at('')
    busd_two_side = StrategyAddTwoSidesOptimalV2.at('')
    btc_two_side = StrategyAddTwoSidesOptimalV2.at('')
    eth_two_side = StrategyAddTwoSidesOptimalV2.at('')
    usdt_two_side = StrategyAddTwoSidesOptimalV2.at('')
    alpha_two_side = StrategyAddTwoSidesOptimalV2.at('')
    uni_two_side = StrategyAddTwoSidesOptimalV2.at('')
    link_two_side = StrategyAddTwoSidesOptimalV2.at('')
    band_two_side = StrategyAddTwoSidesOptimalV2.at('')
    yfi_two_side = StrategyAddTwoSidesOptimalV2.at('')
    front_two_side = StrategyAddTwoSidesOptimalV2.at('')
    dot_two_side = StrategyAddTwoSidesOptimalV2.at('')
    xvs_two_side = StrategyAddTwoSidesOptimalV2.at('')
    inj_two_side = StrategyAddTwoSidesOptimalV2.at('')

    print('done loading two side')

    for i in range(len(fToken_list)):
        new_goblin = new_goblin_list[i]
        new_two_side = new_two_sides[i]

        assert new_two_side.router() == cake_two_side.router(), 'incorrect router'
        assert new_two_side.goblin(
        ) == new_goblin, f'incorrect goblin {new_two_side.goblin()}, {new_goblin}'
        assert new_two_side.fToken_() == new_goblin.fToken(), 'incorrect fToken'
        assert new_two_side.fToken_() == fToken_list[i], 'incorrect fToken'

    ##############################################################
    # deploy new pools

    configs = [
        [True, 6250, 7000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 6250, 7000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 7000, 8000, 11000],
        [True, 5250, 6000, 11000],
        [True, 6250, 7000, 11000],
        [True, 5250, 6000, 11000],
        [True, 6250, 7000, 11000]
    ]

    deploy_indices = list(range(len(fToken_list)))  # all pools
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
        if gobin == cake_goblin:
            goblin.setCriticalStrategies(add_strat_2, liq_strat, {'from': deployer})
            goblin.setStrategyOk([add_strat], False, {'from': deployer})

    # don't add cake to add_strat's whitelist
    add_strat.setWhitelistTokens(deploy_fTokens[1:], [True] * len(deploy_fTokens), {'from': deployer})

    liq_strat.setWhitelistTokens(deploy_fTokens, [True] * len(deploy_fTokens), {'from': deployer})
    rem_strat.setWhitelistTokens(deploy_fTokens, [True] * len(deploy_fTokens), {'from': deployer})

    ##############################################################
    # open positions

    bank.work(0, cake_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [cake_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [cake_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, busd_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [busd_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [busd_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, btc_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [btc_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [btcb_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, eth_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [eth_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [eth_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, usdt_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [usdt_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [usdt_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, alpha_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [alpha_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [alpha_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, band_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [band_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [band_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, link_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [link_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [link_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, yfi_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [yfi_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [yfi_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, uni_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [uni_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [uni_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, front_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [front_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [front_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, dot_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [dot_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [dot_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, xvs_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [xvs_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [xvs_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})
    bank.work(0, inj_goblin, 10**18, 0, eth_abi.encode_abi(['address', 'bytes'], [inj_two_side.address, eth_abi.encode_abi(
        ['address', 'uint256', 'uint256'], [inj_address, 0, 0])]), {'from': deployer, 'value': '2 ether'})

    ##############################################################
    # test work

    # for i in range(len(deploy_goblins)):
    #     goblin = deploy_goblins[i]
    #     add_strat_2 = deploy_two_sides[i]
    #     fToken = deploy_fTokens[i]

    #     test_token(bank, goblin, fToken, add_strat, liq_strat, rem_strat, add_strat_2)
