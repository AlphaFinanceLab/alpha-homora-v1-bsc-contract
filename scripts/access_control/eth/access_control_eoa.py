from brownie import accounts, interface, rpc, network
from ape_safe import ApeSafe
from scripts.utils import SAFE_ETH_EXEC_ADDR

if not rpc.is_active():
    network.priority_fee("1 gwei")
    network.max_fee("60 gwei")

ownable_contracts = [
    "0x67b66c99d3eb37fa76aa3ed1ff33e8e39f0b9c7a",  # bank
    "0x97a49f8eec63c0dfeb9db4c791229477962dc692",  # bank config
    "0x61858a3d3d8fDbC622a64a9fFB5b77Cc57beCB98",  # goblin config
    "0xbebbff645d666445f39900f33201405e1cdaf130",  # IbETHRouter
]
goblins = [
    "0x3c2bbb353b48d54b619db8ac6aa642627fb800e3",
    "0xd902a3bedebad8bead116e8596497cf7d9f45da2",
    "0xf134fdd0bbce951e963d5bc5b0ffe445c9b6c5c6",
    "0xd6419fd982a7651a12a757ca7cd96b969d180330",
    "0x54a2c35d689f4314fa70dd018ea0a84c74506925",
    "0xa7120893283cc2aba8155d6b9887bf228a8a86d2",
    "0xcfbd9eeac76798571ed96ed60ca34df35f29ea8d",
    "0xbb4755673e9df77f1af82f448d2b09f241752c05",
    "0x35952c82e146da5251f2f822d7b679f34ffa71d3",
    "0x8c5cecc9abd8503d167e6a7f2862874b6193e6e4",
    "0x69fe7813f804a11e2fd279eba5dc1ecf6d6bf73b",
    "0x8fc4c0566606aa0c715989928c12ce254f8e1228",
    "0x37ef9c13faa609d5eee21f84e4c6c7bf62e4002e",
    "0x9d9c28f39696ce0ebc42ababd875977060e7afa1",
    "0x5c767dbf81ec894b2d70f2aa9e45a54692d0d7eb",
    "0x6d0eb60d814a21e2bed483c71879777c9217aa28",
    "0x795d3655d0d7ecbf26dd33b1a7676017bb0ee611",
    "0x6a279df44b5717e89b51645e287c734bd3086c1f",
    "0x1001ec1b6fc2438e8be6ffa338d3380237c0399a",
    "0xa8854bd26ee44ad3c78792d68564b96ad0a45245",
    "0x41f07d87a28adec58dba1d063d540b86ccbb989f",
    "0xb7bf6d2e6c4fa291d6073b51911bac17890e92ec",
    "0x4668ff4d478c5459d6023c4a7efda853412fb999",
    "0x14804802592c0f6e2fd03e78ec3efc9b56f1963d",
    "0xdaa93955982d32451f90a1109ecec7fecb7ee4b3",
    "0x4d4ad9628f0c16bbd91cab3a39a8f15f11134300",
    "0x4ec23befb01b9903d58c4bea096d65927e9462cc",
    "0x66e970f2602367f8ae46ccee79f6139737eaff1c",
    "0xcbb95b7708b1b543ecb82b2d58db1711f88d265c",
    "0xfbc0d22bf0ecc735a03fd08fc20b48109cb89543",
    "0xf285e8adf8b871a32c305ab20594cbb251341535",
    "0xe900e07ce6bcdd3c5696bfc67201e940e316c1f1",
    "0xee781f10ce14a45f1d8c2487aeaf24d0366fb9fa",
    "0x09b4608a0ca9ae8002465eb48cd2f916edf5bf63",
    "0x9d00b5eeedeea5141e82b101e645352a2ea960ba",
    "0x0ec3de9941479526bb3f530c23aaff84148d17a7",
    "0x6cc2c08e413638ceb38e3db964a114f139fff81e",
    "0x766614adcff1137f8fced7f0804d184ce659826a",
    "0xcc11e2cf6755953eed483ba2b3c433647d0f18dc",
    "0x18712bcb987785d6679134abc7cddee669ec35ca",
    "0xee8f4e4b13c610bfa2c65d968ba1d5263d640ce6",
    "0xbd95cfef698d4d582e66110475ec7e4e21120e4a",
    "0x9eed7274ea4b614acc217e46727d377f7e6f9b24",
    "0x4354e09bb45ee1edc5ad97b44fa3682ef7e6c77e",
    "0xa4bc927300f174155b95d342488cb2431e7e864e",
    "0xb024b46dcafe360064b3c1c0336c9bb6381d4a7d",
]
strats = [
    "0xb55f46d5bd3e6609b39707afbabd8a61ffed9d0a",
    "0x325a606c8c043ef1e2d07ea6faae543aef7b13cf",
    "0x10329e8b804dae89e535f93e1907274418fd75d8",
    "0xf0cb358be145bdad4f441f6a568f76a3de5a70b7",
    "0x4b1f0ce67303ca233515980219beaeeb389132f7",
    "0xa0fe022d098f92e561aadabe59ab6f15c4a4fe9e",
    "0xea2b4ab299541053152398ee42b0875f2d6870df",
    "0xb004229fc9a8f22aac373923d40ac7f3887863d7",
    "0x8d4958f312ac3009d3804dc659d6a439d34e2821",
    "0xb601361832518d31a18462ce243226811674b987",
    "0x18864491083dc4588a9eecbeb28f22a9bf45dad1",
    "0x587fd08d2979659534d301944b105559ce072ad1",
    "0xbe615dfed36d753999f367458671a4954f7b43e8",
    "0xc207be77051492f89aa7d650a6f03dc76fbf00a6",
    "0xa2d3e7fc0ef83d28fcabc8fb621d8990bfe48115",
    "0x3ecd838f6a5ef357237cdd226bab90255549ec71",
    "0x1c4413ac634d96faee6b64ee98c2bfbcc85dfc4a",
    "0x8448bde9e8643e1adbe610eee0b2efd4b16b830c",
    "0xa8f70a2b021094746ffdeacab15105e5cfe6dc9b",
    "0xd3ea1b6de0ed59bec8b768d2cdc995002c7de95a",
    "0x109bfde650bb8fb7709ceefc2af81013238289fc",
    "0x9f440181f3c8092a5a4c1daa62c8ee3342890762",
    "0x9f73e638a1de6464ad953ec21a12701de10e69cf",
    "0x12a1b67bc18ecb3a4c3b55b527af237bc6596507",
    "0x7cbe919c33abda60248f645b8981b9eb5381ded2",
    "0xedd9d44e302b0bfa693d0179a1ee14dde48306a6",
    "0x1b1db87e728a2c22d596e331caabb0c99790113e",
    "0x1debf8e2ddfc4764376e8e4ed5bc8f1b403d2629",
    "0xa1dc7ce03cb285aca8bde9c27d1e5d4731871814",
    "0xb39f78e505e0959c96a38c91987713bad8519480",
    "0x759034a7e6428430c7383c10b01515ef38b61ed5",
    "0x90b5f08283565de70f7ed78116469abb6b030aea",
    "0x23324a5b4e737440a3b29159bf0b1e39ad93f5a6",
    "0xb96abafe296b51fd245d3c80d2a0e97f933b3285",
    "0x3702bbba321c2fe7be4731f558d2d60fa20eeff9",
    "0xdce3ab478450b101eba5f86b74e014e45d2d385b",
    "0xc99ebcb52c18ff5423d31fd02cf29b4a8069a407",
    "0xf6090bcf0be8e9b256364b015222b2d58bfc8fba",
    "0x3f9dd1b039a19a7cb1dd016527e8566bce185936",
    "0x23091694539a083940eb4236215cc82a619fe475",
    "0x42d7b319807c50f8719698e52315742ad6f00c5a",
    "0xc6d05f8d77a80a04e69ad055ff7f1a599b459ead",
    "0x124fc2970c4dc1cacb813187e6c1a0d2f01c6c53",
    "0xacd4e6d35f96a30c4f7923f95139e275eb783e04",
    "0xd2dadd442727b7172ddab1b73b726a1ef9dbb51f",
    "0xd84f554a24977cf7bda60fc11d6358c432007814",
    "0x483747e40bdb6ab28b4b4ea73b9d62d4d44c509e",
    "0x81796c4602B82054a727527CD16119807b8C7608",
    "0x14f66F8c283D004f4195CD041746B6b5fA823e16",
    "0xf047fbea321de61426437d8ebf5598d7b2673aa6",
    "0x6b4f168e91452a0ac2cff9f4f745f5efad09861c",
    "0x737aad349312f36b43041737d648051a39f146e8",
    "0xc43dc00e5e4cfc8c8092ec4a5d363170c6d14ce9",
    "0xe992e83b268f63ee508c6d292a54dff91c1eb57f",
    "0x942d9e12bc440fe9c374e67dfb0328fb1fbfcd3d",
    "0x58cc5c8e863759ba2aaae2bcaee84ce22404b5e7",
    "0x466c427cc426a88ae2a596ab48a085dd72258354",
]

all_ownable_contracts = ownable_contracts + goblins + strats


def main():
    # FIXME: fix exec address
    exec_account = ApeSafe(SAFE_ETH_EXEC_ADDR)
    eoa_account = accounts.at("0xB593d82d53e2c187dc49673709a6E9f806cdC835", force=True)

    for contract_addr in all_ownable_contracts:
        contract = interface.IAny(contract_addr)
        contract.transferOwnership(exec_account, {"from": eoa_account})

    # testing
    for contract_addr in all_ownable_contracts:
        contract = interface.IAny(contract_addr)
        assert contract.owner() == exec_account

    print("Done!")
