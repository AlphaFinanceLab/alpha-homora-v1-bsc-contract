from brownie import accounts, Contract, chain

try:
    from brownie import interface
except:
    pass

SAFE_BSC_EXEC_ADDR = "0xFdBEbd918A22Fd4D62C1C2239eeE78fB45d55733"

CAKE = "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
ALPHA = "0xa1faa113cbE53436Df28FF0aEe54275c13B40975"
BUSD = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
BYFI = "0x88f1A5ae2A3BF98AEAF342D26B30a79438c9142e"


def almostEqual(a, b, thresh=0.01):
    return a <= b + thresh * abs(b) and a >= b - thresh * abs(b)


def mint_tokens(token, to, interface=None, amount=None):
    if interface is None:
        interface = globals()["interface"]

    token = interface.IAny(token)
    if amount is None:
        # default is 1M tokens
        amount = 10**12 * 10 ** token.decimals()

    if token == CAKE:
        owner = token.owner()
        token.mint(to, amount, {"from": owner})
    elif token == WBNB:
        token.deposit({"from": accounts[9], "value": amount})
        token.transfer(to, amount, {"from": accounts[9]})
    elif token == ALPHA or token == BUSD:
        owner = token.owner()
        token.mint(amount, {"from": owner})
        token.transfer(to, amount, {"from": owner})
    else:
        raise Exception("tokens not supported")


def yes_no_question(message="?", default=False) -> bool:
    """Ask user about yes/no question.

    Argument
    ---------
        message: promt message for showing a question to user.
        default: default answer if user just enter, default is True.

    Return
    ---------
        user's answer: boolean
    """

    answer = "invalid_answer"
    valid_answer = {"yes": True, "y": True, "n": False, "no": False, "": default}
    default_flag_msg = " [Y/n]" if default else " [y/N]"

    while answer not in valid_answer:
        answer = input(message + default_flag_msg).lower()
    return valid_answer[answer]
