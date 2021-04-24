from brownie import accounts, Contract, chain
try:
    from brownie import interface
except:
    pass

CAKE = '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82'
WBNB = '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
ALPHA = '0xa1faa113cbE53436Df28FF0aEe54275c13B40975'
BUSD = '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'
BTC = '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c'
ETH = '0x2170ed0880ac9a755fd29b2688956bd959f933f8'
USDT = '0x55d398326f99059ff775485246999027b3197955'
UNI = '0xbf5140a22578168fd562dccf235e5d43a02ce9b1'
LINK = '0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd'
BAND = '0xad6caeb32cd2c308980a548bd0bc5aa4306c6c18'
YFI = '0x88f1a5ae2a3bf98aeaf342d26b30a79438c9142e'
FRONT = '0x928e55dab735aa8260af3cedada18b5f70c72f1b'
DOT = '0x7083609fce4d1d8dc0c979aab8c869ea2c873402'
XVS = '0xcf6bb5389c92bdda8a3747ddb454cb7a64626c63'
INJ = '0xa2b726b1145a4773f68593cf171187d8ebe4d495'


def almostEqual(a, b, thresh=0.01):
    return a <= b + thresh * abs(b) and a >= b - thresh * abs(b)


def mint_tokens(token, to, interface=None, amount=None):
    if interface is None:
        interface = globals()['interface']

    token = interface.IAny(token)
    if amount is None:
        # default is 1M tokens
        amount = 10**12 * 10**token.decimals()

    if token == CAKE:
        owner = token.owner()
        token.mint(to, amount, {'from': owner})
    elif token == WBNB:
        token.deposit({'from': accounts[9], 'value': amount})
        token.transfer(to, amount, {'from': accounts[9]})
    elif token in [ALPHA, BUSD, BTC, ETH, USDT,  LINK, BAND, YFI, FRONT, DOT,  INJ]:
        owner = token.owner()
        token.mint(amount, {'from': owner})
        token.transfer(to, amount, {'from': owner})
    elif token == UNI:
        owner = token.getOwner()
        token.mint(amount, {'from': owner})
        token.transfer(to, amount, {'from': owner})
    elif token == XVS:
        token.transfer(to, 10**24, {'from': '0xfd36e2c2a6789db23113685031d7f16329158384'})  # distribution address
    else:
        raise Exception('tokens not supported')
