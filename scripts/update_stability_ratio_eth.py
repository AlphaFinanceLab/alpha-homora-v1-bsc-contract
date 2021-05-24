from brownie import interface, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy
from brownie import network
import json


gas_strategy = GasNowScalingStrategy(
    initial_speed="fast", max_speed="fast", increment=1.085, block_duration=20)

# set default gas price
network.gas_price(gas_strategy)

WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
SUSHI = '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2'
MTA = '0xa3BeD4E1c75D00fa6f4E5E6922DB7261B5E9AcD2'
PICKLE = '0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5'


def main():
    deployer = accounts.at('0xB593d82d53e2c187dc49673709a6E9f806cdC835', force=True)
    # deployer = accounts.load('gh')

    goblin_settings = json.load(open('./ahv1_eth_goblin_settings.json'))

    goblin_config = interface.IAny('0x61858a3d3d8fDbC622a64a9fFB5b77Cc57beCB98')
    agg_oracle = interface.IAny(goblin_config.oracle())

    assert agg_oracle.address.lower() == '0x636478DcecA0308ec6b39e3ab1e6b9EBF00Cd01c'.lower(), 'oracle should be agg oracle'

    goblin_list = []
    config_list = []

    for goblin, values in goblin_settings.items():
        goblin = interface.IAny(goblin)
        accept_debt, work_factor, kill_factor, stable_factor = values

        if goblin.address.lower() == '0x3c2BBB353B48D54B619dB8Ac6AA642627Fb800E3'.lower():
            # sushi/eth goblin
            f_token = SUSHI
        elif goblin.address.lower() == '0x4Ec23BeFb01B9903D58C4bEa096d65927E9462cC'.lower():
            # mta/eth goblin
            f_token = MTA
        elif goblin.address.lower() == '0xA8854Bd26ee44Ad3c78792d68564b96ad0a45245'.lower():
            # pickle/eth goblin
            f_token = PICKLE
        else:
            f_token = goblin.fToken()

        if f_token.lower() == '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2'.lower():
            # maker address (problem with symbol)
            symbol = 'MKR'
        else:
            symbol = interface.IAny(f_token).symbol()

        print('===============================')
        print(symbol)

        try:
            price = agg_oracle.getPrice(f_token, WETH)
            assert price != 0
            print('price', price)
        except:
            print(f'cannot get {symbol} price')
            continue

        print('previous config:', values)
        new_config = [accept_debt, work_factor, kill_factor, 11000]  # set stability factor to 1.1x
        print('new values:', new_config)

        goblin_list.append(goblin)
        config_list.append(new_config)

    print('goblin list')
    print(goblin_list)

    print('config_list')
    print(config_list)

    goblin_config.setConfigs(goblin_list, config_list, {'from': deployer})
