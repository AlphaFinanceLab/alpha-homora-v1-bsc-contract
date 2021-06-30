from brownie import accounts, interface, Contract
from brownie import (
    Bank, ConfigurableInterestBankConfig, UniswapGoblin
)
from brownie import network
import eth_abi
from .utils import *

# network.gas_price('5 gwei')
from brownie.network.gas.strategies import GasNowScalingStrategy
gas_strategy = GasNowScalingStrategy(
    initial_speed="fast", max_speed="fast", increment=1.085, block_duration=20)

# set gas strategy
network.gas_price(gas_strategy)


def main():
    deployer = accounts.at(
        '0xb593d82d53e2c187dc49673709a6e9f806cdc835', force=True)
    # deployer = accounts.load('gh')

    # goblin_list = uniswap_goblin_list + sushiswap_goblin_list
    goblin_list = [
        "0xe900e07ce6bcdd3c5696bfc67201e940e316c1f1", "0x35952c82e146da5251f2f822d7b679f34ffa71d3",
        "0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec", "0xa7120893283cc2aba8155d6b9887bf228a8a86d2",
        "0x0ec3de9941479526bb3f530c23aaff84148d17a7", "0x09b4608a0ca9ae8002465eb48cd2f916edf5bf63",
        "0x8c5cecc9abd8503d167e6a7f2862874b6193e6e4", "0xcbb95b7708b1b543ecb82b2d58db1711f88d265c",
        "0x6d0eb60d814a21e2bed483c71879777c9217aa28", "0xfbc0d22bf0ecc735a03fd08fc20b48109cb89543",
        "0x4668ff4d478c5459d6023c4a7efda853412fb999", "0x37ef9c13faa609d5eee21f84e4c6c7bf62e4002e",
        "0xf285e8adf8b871a32c305ab20594cbb251341535", "0x6a279df44b5717e89b51645e287c734bd3086c1f",
        "0x4d4ad9628f0c16bbd91cab3a39a8f15f11134300", "0xd6419fd982a7651a12a757ca7cd96b969d180330",
        "0xf134fdd0bbce951e963d5bc5b0ffe445c9b6c5c6", "0xbb4755673e9df77f1af82f448d2b09f241752c05",
        "0xcc11e2cf6755953eed483ba2b3c433647d0f18dc", "0xee781f10ce14a45f1d8c2487aeaf24d0366fb9fa",
        "0x66e970f2602367f8ae46ccee79f6139737eaff1c", "0x1001ec1b6fc2438e8be6ffa338d3380237c0399a",
        "0x6cc2c08e413638ceb38e3db964a114f139fff81e", "0x4ec23befb01b9903d58c4bea096d65927e9462cc",
        "0x18712bcb987785d6679134abc7cddee669ec35ca", "0x14804802592c0f6e2fd03e78ec3efc9b56f1963d",
        "0xbd95cfef698d4d582e66110475ec7e4e21120e4a", "0x766614adcff1137f8fced7f0804d184ce659826a",
        "0xa8854bd26ee44ad3c78792d68564b96ad0a45245", "0xdaa93955982d32451f90a1109ecec7fecb7ee4b3",
        "0x69fe7813f804a11e2fd279eba5dc1ecf6d6bf73b", "0x9d00b5eeedeea5141e82b101e645352a2ea960ba",
        "0x8fc4c0566606aa0c715989928c12ce254f8e1228", "0x9d9c28f39696ce0ebc42ababd875977060e7afa1",
        "0xee8f4e4b13c610bfa2c65d968ba1d5263d640ce6", "0x54a2c35d689f4314fa70dd018ea0a84c74506925",
        "0x3c2bbb353b48d54b619db8ac6aa642627fb800e3", "0xcfbd9eeac76798571ed96ed60ca34df35f29ea8d",
        "0x5c767dbf81ec894b2d70f2aa9e45a54692d0d7eb", "0x41f07d87a28adec58dba1d063d540b86ccbb989f",
        "0xd902a3bedebad8bead116e8596497cf7d9f45da2", "0x795d3655d0d7ecbf26dd33b1a7676017bb0ee611",
    ]

    all_eth_strat_addr = {
        '0xe900e07ce6bcdd3c5696bfc67201e940e316c1f1': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x35952c82e146da5251f2f822d7b679f34ffa71d3': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # cannot call okStrats
        '0xa7120893283cc2aba8155d6b9887bf228a8a86d2': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x0ec3de9941479526bb3f530c23aaff84148d17a7': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x09b4608a0ca9ae8002465eb48cd2f916edf5bf63': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x8c5cecc9abd8503d167e6a7f2862874b6193e6e4': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x6d0eb60d814a21e2bed483c71879777c9217aa28': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xfbc0d22bf0ecc735a03fd08fc20b48109cb89543': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x4668ff4d478c5459d6023c4a7efda853412fb999': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # cannot call okStrats
        '0x37ef9c13faa609d5eee21f84e4c6c7bf62e4002e': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xf285e8adf8b871a32c305ab20594cbb251341535': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x6a279df44b5717e89b51645e287c734bd3086c1f': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x4d4ad9628f0c16bbd91cab3a39a8f15f11134300': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0xd6419fd982a7651a12a757ca7cd96b969d180330': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xf134fdd0bbce951e963d5bc5b0ffe445c9b6c5c6': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xbb4755673e9df77f1af82f448d2b09f241752c05': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xcc11e2cf6755953eed483ba2b3c433647d0f18dc': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # not found in constant.ts
        '0xee781f10ce14a45f1d8c2487aeaf24d0366fb9fa': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x66e970f2602367f8ae46ccee79f6139737eaff1c': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x1001ec1b6fc2438e8be6ffa338d3380237c0399a': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x6cc2c08e413638ceb38e3db964a114f139fff81e': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        # '0x4ec23befb01b9903d58c4bea096d65927e9462cc': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # no allETHStrat disabled
        '0x18712bcb987785d6679134abc7cddee669ec35ca': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x14804802592c0f6e2fd03e78ec3efc9b56f1963d': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # cannot call okStrats
        '0xbd95cfef698d4d582e66110475ec7e4e21120e4a': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x766614adcff1137f8fced7f0804d184ce659826a': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        # '0xa8854bd26ee44ad3c78792d68564b96ad0a45245': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # no allETHStrat disabled
        '0xdaa93955982d32451f90a1109ecec7fecb7ee4b3': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # cannot call okStrats
        '0x69fe7813f804a11e2fd279eba5dc1ecf6d6bf73b': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x9d00b5eeedeea5141e82b101e645352a2ea960ba': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x8fc4c0566606aa0c715989928c12ce254f8e1228': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x9d9c28f39696ce0ebc42ababd875977060e7afa1': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xee8f4e4b13c610bfa2c65d968ba1d5263d640ce6': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a',
        '0x54a2c35d689f4314fa70dd018ea0a84c74506925': '0x737aad349312f36b43041737d648051a39f146e8',
        # '0x3c2bbb353b48d54b619db8ac6aa642627fb800e3': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # no allETHStrat disabled
        '0xcfbd9eeac76798571ed96ed60ca34df35f29ea8d': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x5c767dbf81ec894b2d70f2aa9e45a54692d0d7eb': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x41f07d87a28adec58dba1d063d540b86ccbb989f': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # cannot call okStrats
        '0xd902a3bedebad8bead116e8596497cf7d9f45da2': '0x737aad349312f36b43041737d648051a39f146e8',
        '0x795d3655d0d7ecbf26dd33b1a7676017bb0ee611': '0x737aad349312f36b43041737d648051a39f146e8',
        '0xcbb95b7708b1b543ecb82b2d58db1711f88d265c': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a'
    }

    add_two_side_opt_strat_addr = {
        '0xe900e07ce6bcdd3c5696bfc67201e940e316c1f1': '0x8de16d5884a418f1034f78045da47f2cae4012a4',
        '0x35952c82e146da5251f2f822d7b679f34ffa71d3': '0x587fd08d2979659534d301944b105559ce072ad1',
        '0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec': '0x1b1db87e728a2c22d596e331caabb0c99790113e', # cannot call okStrats
        '0xa7120893283cc2aba8155d6b9887bf228a8a86d2': '0x8d4958f312ac3009d3804dc659d6a439d34e2821',
        '0x0ec3de9941479526bb3f530c23aaff84148d17a7': '0x42d7b319807c50f8719698e52315742ad6f00c5a',
        '0x09b4608a0ca9ae8002465eb48cd2f916edf5bf63': '0x3f9dd1b039a19a7cb1dd016527e8566bce185936',
        '0x8c5cecc9abd8503d167e6a7f2862874b6193e6e4': '0xbe615dfed36d753999f367458671a4954f7b43e8',
        '0x6d0eb60d814a21e2bed483c71879777c9217aa28': '0xa8f70a2b021094746ffdeacab15105e5cfe6dc9b',
        '0xfbc0d22bf0ecc735a03fd08fc20b48109cb89543': '0x3702bbba321c2fe7be4731f558d2d60fa20eeff9',
        '0x4668ff4d478c5459d6023c4a7efda853412fb999': '0x1debf8e2ddfc4764376e8e4ed5bc8f1b403d2629', # cannot call okStrats
        '0x37ef9c13faa609d5eee21f84e4c6c7bf62e4002e': '0x3ecd838f6a5ef357237cdd226bab90255549ec71',
        '0xf285e8adf8b871a32c305ab20594cbb251341535': '0xdce3ab478450b101eba5f86b74e014e45d2d385b',
        '0x6a279df44b5717e89b51645e287c734bd3086c1f': '0x109bfde650bb8fb7709ceefc2af81013238289fc',
        '0x4d4ad9628f0c16bbd91cab3a39a8f15f11134300': '0x759034a7e6428430c7383c10b01515ef38b61ed5',
        '0xd6419fd982a7651a12a757ca7cd96b969d180330': '0xea2b4ab299541053152398ee42b0875f2d6870df',
        '0xf134fdd0bbce951e963d5bc5b0ffe445c9b6c5c6': '0xa0fe022d098f92e561aadabe59ab6f15c4a4fe9e',
        '0xbb4755673e9df77f1af82f448d2b09f241752c05': '0x18864491083dc4588a9eecbeb28f22a9bf45dad1',
        '0xcc11e2cf6755953eed483ba2b3c433647d0f18dc': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', # not found in constant.ts
        '0xee781f10ce14a45f1d8c2487aeaf24d0366fb9fa': '0xf6090bcf0be8e9b256364b015222b2d58bfc8fba',
        '0x66e970f2602367f8ae46ccee79f6139737eaff1c': '0x23324a5b4e737440a3b29159bf0b1e39ad93f5a6',
        '0x1001ec1b6fc2438e8be6ffa338d3380237c0399a': '0x9f440181f3c8092a5a4c1daa62c8ee3342890762',
        '0x6cc2c08e413638ceb38e3db964a114f139fff81e': '0xc6d05f8d77a80a04e69ad055ff7f1a599b459ead',
        '0x4ec23befb01b9903d58c4bea096d65927e9462cc': '0x90b5f08283565de70f7ed78116469abb6b030aea',
        '0x18712bcb987785d6679134abc7cddee669ec35ca': '0xd2dadd442727b7172ddab1b73b726a1ef9dbb51f',
        '0x14804802592c0f6e2fd03e78ec3efc9b56f1963d': '0xa1dc7ce03cb285aca8bde9c27d1e5d4731871814', # cannot call okStrats
        '0xbd95cfef698d4d582e66110475ec7e4e21120e4a': '0x483747e40bdb6ab28b4b4ea73b9d62d4d44c509e',
        '0x766614adcff1137f8fced7f0804d184ce659826a': '0x124fc2970c4dc1cacb813187e6c1a0d2f01c6c53',
        '0xa8854bd26ee44ad3c78792d68564b96ad0a45245': '0x9f73e638a1de6464ad953ec21a12701de10e69cf',
        '0xdaa93955982d32451f90a1109ecec7fecb7ee4b3': '0xb39f78e505e0959c96a38c91987713bad8519480', # cannot call okStrats
        '0x69fe7813f804a11e2fd279eba5dc1ecf6d6bf73b': '0xc207be77051492f89aa7d650a6f03dc76fbf00a6',
        '0x9d00b5eeedeea5141e82b101e645352a2ea960ba': '0x23091694539a083940eb4236215cc82a619fe475',
        '0x8fc4c0566606aa0c715989928c12ce254f8e1228': '0xa2d3e7fc0ef83d28fcabc8fb621d8990bfe48115',
        '0x9d9c28f39696ce0ebc42ababd875977060e7afa1': '0x1c4413ac634d96faee6b64ee98c2bfbcc85dfc4a',
        '0xee8f4e4b13c610bfa2c65d968ba1d5263d640ce6': '0xd84f554a24977cf7bda60fc11d6358c432007814',
        '0x54a2c35d689f4314fa70dd018ea0a84c74506925': '0xb004229fc9a8f22aac373923d40ac7f3887863d7',
        '0x3c2bbb353b48d54b619db8ac6aa642627fb800e3': '0x325a606c8c043ef1e2d07ea6faae543aef7b13cf',
        '0xcfbd9eeac76798571ed96ed60ca34df35f29ea8d': '0xb601361832518d31a18462ce243226811674b987',
        '0x5c767dbf81ec894b2d70f2aa9e45a54692d0d7eb': '0x8448bde9e8643e1adbe610eee0b2efd4b16b830c',
        '0x41f07d87a28adec58dba1d063d540b86ccbb989f': '0xedd9d44e302b0bfa693d0179a1ee14dde48306a6', # cannot call okStrats
        '0xd902a3bedebad8bead116e8596497cf7d9f45da2': '0x4b1f0ce67303ca233515980219beaeeb389132f7',
        '0x795d3655d0d7ecbf26dd33b1a7676017bb0ee611': '0xd3ea1b6de0ed59bec8b768d2cdc995002c7de95a',
        '0xcbb95b7708b1b543ecb82b2d58db1711f88d265c': '0xb96abafe296b51fd245d3c80d2a0e97f933b3285'
    }

    contracts_no_ok_strats_to_check = set([
        '0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec', '0x4668ff4d478c5459d6023c4a7efda853412fb999',
        '0x14804802592c0f6e2fd03e78ec3efc9b56f1963d', '0xdaa93955982d32451f90a1109ecec7fecb7ee4b3',
        '0x41f07d87a28adec58dba1d063d540b86ccbb989f'
    ])

    goblins = {x: UniswapGoblin.at(x) for x in goblin_list}
    print('mapping goblins success')
    
    print('checking if strats are already disabled')
    for goblin_addr in goblin_list:
        if goblin_addr in contracts_no_ok_strats_to_check:
            continue

        if goblin_addr in all_eth_strat_addr:
            assert goblins[goblin_addr].okStrats(all_eth_strat_addr[goblin_addr]) == True, (
                f'all-eth strategy has already been disabled in {goblin_addr}'
            )
        if goblin_addr in add_two_side_opt_strat_addr:
            assert goblins[goblin_addr].okStrats(add_two_side_opt_strat_addr[goblin_addr]) == True, (
                f'add-two-side-opt strategy has already been disabled in {goblin_addr}'
            )

    print('disable allETHOnly and addTwoSidesOptimal strategy')
    for goblin_addr, goblin in goblins.items():
        strategies = []
        if goblin_addr in all_eth_strat_addr:
            strategies.append(all_eth_strat_addr[goblin_addr])
        if goblin_addr in add_two_side_opt_strat_addr:
            strategies.append(add_two_side_opt_strat_addr[goblin_addr])
        goblin.setStrategyOk(strategies, False, {'from': deployer})

    print("Done!!!")
    print("End of deploy process!!!")

    # ###########################################################
    # # test opening strats
    print('==========================================')
    print('start testing')

    alice = accounts[0]
    print('execute allbnb strategies; expect all error')
    bank = Bank.at('0x67b66c99d3eb37fa76aa3ed1ff33e8e39f0b9c7a')
    tokens_for_goblin = {
        '0xe900e07ce6bcdd3c5696bfc67201e940e316c1f1': '0x8de16d5884a418f1034f78045da47f2cae4012a4',
        '0x35952c82e146da5251f2f822d7b679f34ffa71d3': '0x587fd08d2979659534d301944b105559ce072ad1',
        '0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec': '0x1b1db87e728a2c22d596e331caabb0c99790113e', 
        '0xa7120893283cc2aba8155d6b9887bf228a8a86d2': '0x8d4958f312ac3009d3804dc659d6a439d34e2821',
        '0x0ec3de9941479526bb3f530c23aaff84148d17a7': '0x42d7b319807c50f8719698e52315742ad6f00c5a',
        '0x09b4608a0ca9ae8002465eb48cd2f916edf5bf63': '0x3f9dd1b039a19a7cb1dd016527e8566bce185936',
        '0x8c5cecc9abd8503d167e6a7f2862874b6193e6e4': '0xbe615dfed36d753999f367458671a4954f7b43e8',
        '0x6d0eb60d814a21e2bed483c71879777c9217aa28': '0xa8f70a2b021094746ffdeacab15105e5cfe6dc9b',
        '0xfbc0d22bf0ecc735a03fd08fc20b48109cb89543': '0x3702bbba321c2fe7be4731f558d2d60fa20eeff9',
        '0x4668ff4d478c5459d6023c4a7efda853412fb999': '0x1debf8e2ddfc4764376e8e4ed5bc8f1b403d2629', 
        '0x37ef9c13faa609d5eee21f84e4c6c7bf62e4002e': '0x3ecd838f6a5ef357237cdd226bab90255549ec71',
        '0xf285e8adf8b871a32c305ab20594cbb251341535': '0xdce3ab478450b101eba5f86b74e014e45d2d385b',
        '0x6a279df44b5717e89b51645e287c734bd3086c1f': '0x109bfde650bb8fb7709ceefc2af81013238289fc',
        '0x4d4ad9628f0c16bbd91cab3a39a8f15f11134300': '0x759034a7e6428430c7383c10b01515ef38b61ed5',
        '0xd6419fd982a7651a12a757ca7cd96b969d180330': '0xea2b4ab299541053152398ee42b0875f2d6870df',
        '0xf134fdd0bbce951e963d5bc5b0ffe445c9b6c5c6': '0xa0fe022d098f92e561aadabe59ab6f15c4a4fe9e',
        '0xbb4755673e9df77f1af82f448d2b09f241752c05': '0x18864491083dc4588a9eecbeb28f22a9bf45dad1',
        '0xcc11e2cf6755953eed483ba2b3c433647d0f18dc': '0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a', 
        '0xee781f10ce14a45f1d8c2487aeaf24d0366fb9fa': '0xf6090bcf0be8e9b256364b015222b2d58bfc8fba',
        '0x66e970f2602367f8ae46ccee79f6139737eaff1c': '0x23324a5b4e737440a3b29159bf0b1e39ad93f5a6',
        '0x1001ec1b6fc2438e8be6ffa338d3380237c0399a': '0x9f440181f3c8092a5a4c1daa62c8ee3342890762',
        '0x6cc2c08e413638ceb38e3db964a114f139fff81e': '0xc6d05f8d77a80a04e69ad055ff7f1a599b459ead',
        '0x4ec23befb01b9903d58c4bea096d65927e9462cc': '0x90b5f08283565de70f7ed78116469abb6b030aea',
        '0x18712bcb987785d6679134abc7cddee669ec35ca': '0xd2dadd442727b7172ddab1b73b726a1ef9dbb51f',
        '0x14804802592c0f6e2fd03e78ec3efc9b56f1963d': '0xa1dc7ce03cb285aca8bde9c27d1e5d4731871814', 
        '0xbd95cfef698d4d582e66110475ec7e4e21120e4a': '0x483747e40bdb6ab28b4b4ea73b9d62d4d44c509e',
        '0x766614adcff1137f8fced7f0804d184ce659826a': '0x124fc2970c4dc1cacb813187e6c1a0d2f01c6c53',
        '0xa8854bd26ee44ad3c78792d68564b96ad0a45245': '0x9f73e638a1de6464ad953ec21a12701de10e69cf',
        '0xdaa93955982d32451f90a1109ecec7fecb7ee4b3': '0xb39f78e505e0959c96a38c91987713bad8519480', 
        '0x69fe7813f804a11e2fd279eba5dc1ecf6d6bf73b': '0xc207be77051492f89aa7d650a6f03dc76fbf00a6',
        '0x9d00b5eeedeea5141e82b101e645352a2ea960ba': '0x23091694539a083940eb4236215cc82a619fe475',
        '0x8fc4c0566606aa0c715989928c12ce254f8e1228': '0xa2d3e7fc0ef83d28fcabc8fb621d8990bfe48115',
        '0x9d9c28f39696ce0ebc42ababd875977060e7afa1': '0x1c4413ac634d96faee6b64ee98c2bfbcc85dfc4a',
        '0xee8f4e4b13c610bfa2c65d968ba1d5263d640ce6': '0xd84f554a24977cf7bda60fc11d6358c432007814',
        '0x54a2c35d689f4314fa70dd018ea0a84c74506925': '0xb004229fc9a8f22aac373923d40ac7f3887863d7',
        '0x3c2bbb353b48d54b619db8ac6aa642627fb800e3': '0x325a606c8c043ef1e2d07ea6faae543aef7b13cf',
        '0xcfbd9eeac76798571ed96ed60ca34df35f29ea8d': '0xb601361832518d31a18462ce243226811674b987',
        '0x5c767dbf81ec894b2d70f2aa9e45a54692d0d7eb': '0x8448bde9e8643e1adbe610eee0b2efd4b16b830c',
        '0x41f07d87a28adec58dba1d063d540b86ccbb989f': '0xedd9d44e302b0bfa693d0179a1ee14dde48306a6', 
        '0xd902a3bedebad8bead116e8596497cf7d9f45da2': '0x4b1f0ce67303ca233515980219beaeeb389132f7',
        '0x795d3655d0d7ecbf26dd33b1a7676017bb0ee611': '0xd3ea1b6de0ed59bec8b768d2cdc995002c7de95a',
        '0xcbb95b7708b1b543ecb82b2d58db1711f88d265c': '0xb96abafe296b51fd245d3c80d2a0e97f933b3285'
    }
    for goblin_addr in goblins.keys():
        if goblin_addr not in all_eth_strat_addr:
            continue
        print('check', goblin_addr)
        try:
            bank.work(
                0,
                goblin_addr,
                0,
                0,
                eth_abi.encode_abi(
                    ['address', 'bytes'],
                    [
                        all_eth_strat_addr[goblin_addr],
                        eth_abi.encode_abi(['address', 'uint'], [tokens_for_goblin[goblin_addr], 0])
                    ]
                ),
                {'from': alice, 'value': '1 ether'}
            )
            assert False, 'the above command should be reverted'
        except Exception as err:
            print('got error as expect!!!')
            assert "unapproved work strategy" in str(err), (
                f'incorrect msg error; got {err}'
            )

    print('execute addTwoSidesOptimal strategy; expect error')
    for goblin_addr in goblins.keys():
        if goblin_addr not in add_two_side_opt_strat_addr:
            continue
        print('check', goblin_addr)
        try:
            bank.work(
                0,
                goblin_addr,
                0,
                0,
                eth_abi.encode_abi(
                    ['address', 'bytes'],
                    [
                        add_two_side_opt_strat_addr[goblin_addr],
                        eth_abi.encode_abi(['address', 'uint', 'uint'], [tokens_for_goblin[goblin_addr], 0, 0])
                    ]
                ),
                {'from': alice, 'value': '1 ether'}
            )
            assert False, 'the above command should be reverted'
        except Exception as err:
            print('got error as expect!!!')
            assert "unapproved work strategy" in str(err), (
                f'incorrect msg error; got {err}'
            )

    print('End of testing!!!')
