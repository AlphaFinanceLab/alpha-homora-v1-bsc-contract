from brownie import accounts, interface, Contract
from brownie import (TripleSlopeModel, ConfigurableInterestBankConfig, Bank,
                     IbBNBRouter, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from .utils import *
from .constant import *


def main():
    admin = accounts[0]
    alice = accounts[1]
    minter = accounts[9]

    alpha = interface.IAny(alpha_address)
    pancake_router = interface.IAny(router_address)

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

    # create pair
    factory = interface.IAny(interface.IAny(router_address).factory())
    factory.createPair(alpha_address, bank, {'from': minter})

    # deploy ibBNBRouter
    router = IbBNBRouter.deploy(router_address, bank, alpha_address, {'from': admin})

    # get ibBNB + ALPHA to minter
    bank.deposit({'from': minter, 'value': '100000 ether'})
    mint_tokens(alpha_address, minter)

    # mint ibBNB + ALPHA to alice
    bank.transfer(alice, 1000 * 10**18, {'from': minter})
    mint_tokens(alpha_address, alice)

    # minter approve pancake router
    alpha.approve(router_address, 2**256-1, {'from': minter})
    bank.approve(router_address, 2**256-1, {'from': minter})

    # alice approve ibBNB router
    alpha.approve(router, 2**256-1, {'from': alice})
    bank.approve(router, 2**256-1, {'from': alice})
    lp = interface.IAny(router.lpToken())
    lp.approve(router, 2**256-1, {'from': alice})

    # setup liquidity in ibBNB + ALPHA pool
    price = 1000  # 1 ibBNB = 1000 alpha
    bnb_supply = 1000 * 10**18
    pancake_router.addLiquidity(bank, alpha_address, bnb_supply,
                                bnb_supply * price, 0, 0, minter, 2**256-1, {'from': minter})

    ##############################################################################################
    # Case 1. add & remove liquidity alpha + bnb
    print('======================================================================')
    print('Case 1. add liquidity & remove alpha + bnb')

    prevBNBBal = alice.balance()

    # add liquidity
    router.addLiquidityBNB(10**18, 0, 0, alice, 2**256-1, {'from': alice, 'value': 10**18})

    curBNBBal = alice.balance()

    delta1 = curBNBBal - prevBNBBal

    assert lp.balanceOf(alice) > 0

    prevBNBBal = alice.balance()

    # remove liquidity
    router.removeLiquidityBNB(lp.balanceOf(alice), 0, 0, alice, 2**256-1, {'from': alice})

    curBNBBal = alice.balance()

    delta2 = curBNBBal - prevBNBBal

    assert almostEqual(delta1, -10**18 // price), 'incorrect BNB input amount'
    assert almostEqual(delta2, 10**18 // price), 'incorrect BNB output amount'

    ##############################################################################################
    # Case 2. add liquidity two sides optimal
    print('======================================================================')
    print('Case 2. add liquidity two sides optimal')

    prevIbBNBBal = bank.balanceOf(alice)
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimal(10**18, 0, 0, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curIbBNBBal - prevIbBNBBal, -10**18), 'incorrect ibBNB input amount'

    prevIbBNBBal = bank.balanceOf(alice)
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimal(0, 10**18, 0, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curAlphaBal - prevAlphaBal, -10**18), 'incorrect ALPHA input amount'

    prevIbBNBBal = bank.balanceOf(alice)
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimal(2 * 10**18, 10**18, 0, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curIbBNBBal - prevIbBNBBal, -2 * 10**18), 'incorrect ibBNB input amount'
    assert almostEqual(curAlphaBal - prevAlphaBal, -10**18), 'incorrect ALPHA input amount'

    ##############################################################################################
    # Case 3. add liquidity two sides optimal bnb
    print('======================================================================')
    print('Case 3. add liquidity two sides optimal bnb')

    prevIbBNBBal = bank.balanceOf(alice)
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimalBNB(10**18, 0, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curAlphaBal - prevAlphaBal, -10**18), 'incorrect ALPHA input amount'

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimalBNB(
        0, 0, alice, 2**256-1, {'from': alice, 'value': '1 ether'})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect ibBNB input amount'

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.addLiquidityTwoSidesOptimalBNB(
        2 * 10**18, 0, alice, 2**256-1, {'from': alice, 'value': '1 ether'})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curBNBBal - prevBNBBal, -10**18), 'incorrect ibBNB input amount'
    assert almostEqual(curAlphaBal - prevAlphaBal, -2 * 10**18), 'incorrect ALPHA input amount'

    ##############################################################################################
    # Case 4. remove liquidity alpha + bnb
    print('======================================================================')
    print('Case 4. remove liquidity alpha + bnb')

    r0, r1, _ = lp.getReserves()
    supply = lp.totalSupply()

    prevLPBal = lp.balanceOf(alice)
    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.removeLiquidityBNB(lp.balanceOf(alice) // 10, 0, 0, alice, 2**256-1, {'from': alice})

    curLPBal = lp.balanceOf(alice)
    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curLPBal - prevLPBal, -prevLPBal // 10), 'incorrect LP withdraw amount'
    assert almostEqual(curAlphaBal - prevAlphaBal, r0 * prevLPBal //
                       10 / supply), 'incorrect ALPHA received'
    assert almostEqual(curBNBBal - prevBNBBal, r1 * prevLPBal //
                       10 / supply), 'incorrect BNB received'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'

    ##############################################################################################
    # Case 5. remove liquidity all alpha
    print('======================================================================')
    print('Case 5. remove liquidity all alpha')

    r0, r1, _ = lp.getReserves()
    supply = lp.totalSupply()

    prevLPBal = lp.balanceOf(alice)
    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.removeLiquidityAllAlpha(lp.balanceOf(alice) // 10, 0,
                                   alice, 2**256-1, {'from': alice})

    curLPBal = lp.balanceOf(alice)
    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curLPBal - prevLPBal, -prevLPBal // 10), 'incorrect LP withdraw amount'
    assert almostEqual(curAlphaBal - prevAlphaBal, 2 * r0 * prevLPBal //
                       10 / supply), 'incorrect ALPHA received'
    assert curBNBBal == prevBNBBal, 'BNB not equal'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'

    ##############################################################################################
    # Case 6. swap exact bnb for alpha
    print('======================================================================')
    print('Case 6. swap exact bnb for alpha')

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.swapExactBNBForAlpha(0, alice, 2**256-1, {'from': alice, 'value': '1 ether'})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curAlphaBal - prevAlphaBal, 10**18 * price), 'incorrect ALPHA received'
    assert curBNBBal - prevBNBBal == -10**18, 'BNB not equal'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'

    ##############################################################################################
    # Case 7. swap alpha for exact bnb
    print('======================================================================')
    print('Case 7. swap alpha for exact bnb')

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.swapAlphaForExactBNB(10**16, 2000 * 10**16, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert almostEqual(curAlphaBal - prevAlphaBal, -10**16 * price), 'incorrect ALPHA received'
    assert curBNBBal - prevBNBBal == 10**16, 'BNB not equal'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'

    ##############################################################################################
    # Case 8. swap exact alpha for bnb
    print('======================================================================')
    print('Case 8. swap exact alpha for bnb')

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.swapExactAlphaForBNB(10**18, 0, alice, 2**256-1, {'from': alice})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert curAlphaBal - prevAlphaBal == -10**18, 'incorrect ALPHA received'
    assert almostEqual(curBNBBal - prevBNBBal, 10**18 // price), 'BNB not equal'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'

    ##############################################################################################
    # Case 9. swap bnb for exact alpha
    print('======================================================================')
    print('Case 9. swap bnb for exact alpha')

    prevIbBNBBal = bank.balanceOf(alice)
    prevBNBBal = alice.balance()
    prevAlphaBal = alpha.balanceOf(alice)

    router.swapBNBForExactAlpha(10**18, alice, 2**256-1, {'from': alice, 'value': '1 ether'})

    curIbBNBBal = bank.balanceOf(alice)
    curBNBBal = alice.balance()
    curAlphaBal = alpha.balanceOf(alice)

    assert curAlphaBal - prevAlphaBal == 10**18, 'incorrect ALPHA received'
    assert almostEqual(curBNBBal - prevBNBBal, -10**18 // price), 'BNB not equal'
    assert prevIbBNBBal == curIbBNBBal, 'ibBNB not equal'
