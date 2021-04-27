from brownie import accounts, interface, Contract
from brownie import PancakeswapGoblinConfig, ConfigurableInterestBankConfig
from brownie import network

network.gas_price('5 gwei')


def main():
    deployer = accounts.at('0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58', force=True)
    # deployer = accounts.load('ghb')

    bank_config = ConfigurableInterestBankConfig.at('0x70DF43522D3a7332310b233De763758adCa14961')
    goblin_config = PancakeswapGoblinConfig.at('0x8703f72dbdcd169a9c702e7044603ebbfb11425c')

    goblin_v1_list = [
        '0xaa00f2b7dd0de46c6fc9655dbadd80ac91a66869',  # cake
        '0x08d871ddad70bd3aef3fecfbf4350debc57d8264',  # busd
        '0x549ef362657a3e3923793a494db3d89e3e5fda35',  # btc
        '0x2f050b64ede3b1d21184435974bb1d2fe02012b6',  # eth
        '0x3974071481dad49ac94ca1756f311c872ec3e26e',  # usdt
        '0xfdcdf8d07db8c5b33fbf46f41eced421d9d32bee',  # uni
        '0x047683a9a7958c02ca86b6eecea1f8acfbd54f4f',  # link
        '0xc3c16508e77e99e67cfcd30b765e48a5a33d4c9d',  # band
        '0x3663aedebb70dcf0a64e2600233d6913dd3ecf2b',  # yfi
        '0xa0aa119e0324d864831c24b78e85927526e42d52',  # alpha
        '0x62e32e6ebeabf776b59f5dfb9b364779c3a64137',  # inj
        '0x567f4a45d45945a75898be4cad299a8f32c86d08',  # dot
        '0xd6d8f5e06f655ff01bb3b08dd65946babbfec351',  # xvs
        '0x3cab9d2ca781c6b6cf8d29bfb450aa4fffcae854',  # front
    ]

    # check if goblin is goblin, and pid < 251 (v1 pools)
    for goblin in goblin_v1_list:
        assert bank_config.isGoblin(goblin), f'{goblin} is not goblin'
        assert interface.IAny(goblin).pid() < 251, 'goblin pid >= 251 (v2 pools)'

    print('done checking...')

    configs = []

    for goblin in goblin_v1_list:
        r0, r1, r2, r3 = goblin_config.goblins(goblin)

        assert r0, f'{goblin} goblin accept debt was false'
        config = (False, r1, r2, r3)
        configs.append(config)

    goblin_config.setConfigs(goblin_v1_list, configs, {'from': deployer})

    for goblin in goblin_v1_list:
        print(goblin_config.goblins(goblin))
