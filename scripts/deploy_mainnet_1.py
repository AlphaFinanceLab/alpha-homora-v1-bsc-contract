from brownie import accounts, interface, Contract
from brownie import (Bank, SimpleBankConfig, SimplePriceOracle, PancakeswapGoblin,
                     StrategyAllBNBOnly, StrategyLiquidate, StrategyWithdrawMinimizeTrading, StrategyAddTwoSidesOptimal, PancakeswapGoblinConfig, TripleSlopeModel, ConfigurableInterestBankConfig, PancakeswapPool1Goblin, ProxyAdminImpl, TransparentUpgradeableProxyImpl)
from brownie import network
from .utils import *
from .constant import *
import eth_abi

# set default gas price
network.gas_price('10 gwei')


def main():
    triple_slope_model = TripleSlopeModel.deploy({'from': deployer})

    # min debt 1 BNB at 10 gwei gas price (avg gas fee = ~0.006 BNB) (killBps 1% -> at least 0.01BNB bonus)
    # reserve pool bps 2000 (20%)
    # kill bps 100 (1%)
    bank_config = ConfigurableInterestBankConfig.deploy(
        10**18, 2000, 100, triple_slope_model, {'from': deployer})

    bank_impl = Bank.deploy({'from': deployer})
