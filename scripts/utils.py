from brownie import accounts, Contract, chain
try:
    from brownie import interface
except:
    pass

CAKE = '0xa1c8dff968533b1b2bbadf14e84a211531d57c34'
WBNB = '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'


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
