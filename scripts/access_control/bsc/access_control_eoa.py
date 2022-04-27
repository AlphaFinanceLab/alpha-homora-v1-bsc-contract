from brownie import accounts, ProxyAdminImpl, interface, Governable, Bank
from brownie.exceptions import VirtualMachineError
from ape_safe import ApeSafe

ownable_contracts = [
    "0x70df43522d3a7332310b233de763758adca14961",  # bank config
    "0x8703f72dbdCD169A9C702E7044603ebbfb11425c",  # goblin config
]
goblins = [
    "0x5a71a15037de71d52d8b27b6a637b617b4fae261",
    "0xa25ad83285e0d0989b1409b3755be7e30bb821d7",
    "0x44ae9dfaf7597c3665fb25ed31b5a32bab12ebc4",
    "0x1601b34b8ae3378c7c2df675a37a7064164c74ca",
    "0x22bb68bd0b113ccf688e0759ac0b4abc013df824",
    "0xc07e4cc403b093bd94d80f30c78b63080a79cd10",
    "0x8252aa78372b59d53e1c001d98f400611e9d2a20",
    "0x7b4b9e3d52296416b7e0396593b5d885cdb27472",
    "0x7e52d9dbaf0366aaec36175d551b21762336ecdb",
    "0x78cffa390b2355b14aacaf97571da3be817c84bf",
    "0xc2dc871a7ded817d8a960d2f2ceae6edb377c73f",
    "0xaef73ea3a6f3f302af20a154c68996790bbaa85e",
    "0x8f543b602e0bf1cc652c10f50d0ad853185a5f26",
    "0xcd168c28c17aef8d47b88ff0904ef5bf1c806000",
    "0xaa00f2b7dd0de46c6fc9655dbadd80ac91a66869",
    "0x08d871ddad70bd3aef3fecfbf4350debc57d8264",
    "0x549ef362657a3e3923793a494db3d89e3e5fda35",
    "0x2f050b64ede3b1d21184435974bb1d2fe02012b6",
    "0x3974071481dad49ac94ca1756f311c872ec3e26e",
    "0xfdcdf8d07db8c5b33fbf46f41eced421d9d32bee",
    "0x047683a9a7958c02ca86b6eecea1f8acfbd54f4f",
    "0xc3c16508e77e99e67cfcd30b765e48a5a33d4c9d",
    "0x3663aedebb70dcf0a64e2600233d6913dd3ecf2b",
    "0xa0aa119e0324d864831c24b78e85927526e42d52",
    "0x62e32e6ebeabf776b59f5dfb9b364779c3a64137",
    "0x567f4a45d45945a75898be4cad299a8f32c86d08",
    "0x3cab9d2ca781c6b6cf8d29bfb450aa4fffcae854",
    "0xd6d8f5e06f655ff01bb3b08dd65946babbfec351",
]

strats = [
    "0x27d7dc4bfb0239376b7a597d130dd66eec97137f",
    "0xbe248ef29f305ccec46fd1f503b84c026776f4a9",
    "0x19d5a28b946656728317ae40a5d7b8a0d91a95a0",
    "0x951196356083970429718342f380fdac9a7e80f0",
    "0xd6fa7a3ed180f2fc94af35c04416c5becc78a008",
    "0x62370d842a5c52d64a152063e39fc4a3f7877b57",
    "0x6df2c20dda922f2844d2d95f45c49a77efb3bb67",
    "0x57b81ae30e356fdcf4aee6911f2242a3b37a89ad",
    "0x3c073bd655b0687fe576217a68cb28a483b0c894",
    "0xb14c30fa44b45078ae874fb36561cd7ff7207a1c",
    "0xf6e26ccacb6115282faf732ff61bdc6e72f32f9c",
    "0x6ab62fc9a84850f2ff005704da7c32f3e5630dce",
    "0xf3bce1883226a67d2a22f17720f715cde2b7b884",
    "0x59ed76bae09f53f8c4f3bf0e26cb5ee695ce767c",
    "0x10cfc0bafec90be55a22b6b6ae30f609a64be4dc",
    "0xa51dcfa00f7a0289114973d44e7fce053fff0309",
    "0xf26c49e822c9b51aaac71c15572d3b94c21e3165",
    "0x06a34a95b3e1064295e93e9c92c15a4ebfed7eef",
    "0x93db96377706693b0c4548efaddb73dce4a3f14b",
    "0x034c0d2b94a2b843c3cccae6be0f74f44b5dd3f9",
    "0xbd1c05cbe5f7c625bb7877caa23ba461abae4887",
    "0x1805f590c13ec9c59a197400f56b4b0d1adec796",
    "0x8240600913c1a8b3d80b29245d94f2af09facac8",
    "0x40bdfa199ef27143f0ce292a162450cf5512c390",
    "0x7fcae7fd3cb010c30751420a2553bc8232923eae",
    "0x397f4605b953134f2cf5f1176a25a7f5171c2925",
    "0xbd6600922422fd84f02b47b40cd83a4f25d1b12d",
    "0xdda8648fbfed2f2abd0dfca404c7d8f154ccb8b7",
    "0x44a819a0d93849bd6587cd6000e91bf8b302deaa",
    "0xb8bd068dd234d9cc06763cfbcea53ecd60e82b8d",
    "0xa39844d2d8fb827693d3f8e96abd8596f8ebaede",
    "0xf8935dbd2877ac69e25fbdae3003bff391ca0357",
    "0xe15e4a5c2b6ea78cc12e7d320b732924b64e6137",
    "0xe47b5464a7860efd6486094f91c034a180108424",
]

all_governable_contracts = [
    "0x3bb5f6285c312fc7e1877244103036ebbeda193d",  # bank
]
all_ownable_contracts = ownable_contracts + goblins + strats


def main():
    # FIXME: fix exec address
    exec_safe = ApeSafe("0x6be987c6d72e25F02f6f061F94417d83a6Aa13fC")
    exec_account = exec_safe.account
    eoa_account = accounts.at("0x4D4DA0D03F6f087697bbf13378a21E8ff6aF1a58", force=True)

    proxy_admin = ProxyAdminImpl.at("0x74168a07c24f9d40ccf3d16ad18df9caa7b50841")

    ownable_contracts.extend(goblins + strats)

    proxy_admin.transferOwnership(exec_account, {"from": eoa_account})

    for contract_addr in all_governable_contracts:
        contract = Governable.at(contract_addr)
        contract.setPendingGovernor(exec_account, {"from": eoa_account})

    for contract_addr in all_ownable_contracts:
        contract = interface.IAny(contract_addr)
        contract.transferOwnership(exec_account, {"from": eoa_account})

    # testing
    assert proxy_admin.owner() == exec_account
    # try to upgrade bank
    mock_bank_impl = Bank.deploy({"from": eoa_account})
    proxy_admin.upgrade(
        "0x3bb5f6285c312fc7e1877244103036ebbeda193d",
        mock_bank_impl,
        {"from": exec_account},
    )
    try:
        proxy_admin.upgrade(
            "0x3bb5f6285c312fc7e1877244103036ebbeda193d",
            mock_bank_impl,
            {"from": eoa_account},
        )
    except VirtualMachineError as e:
        assert e.revert_msg == "Ownable: caller is not the owner"
        print(e)

    for contract_addr in ownable_contracts:
        contract = interface.IAny(contract_addr)
        assert contract.owner() == exec_account

    print("Done!")
