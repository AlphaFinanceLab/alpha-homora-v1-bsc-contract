# AlphaHomora 💫 🔐

**Unlock Your Yield Farming Potential**

The repository contains the smart contracts of [AlphaHomora](https://homora.alphafinance.io) leveraged yield farming protocol on [Ethereum](https://ethereum.org/) and [Binance Smart Chain](https://www.binance.org/en/smartChain) and any other EVM compatible blockchains you like. With AlphaHomora, the lenders can earn interests on supplied blockchain native currencies (i.e. ETH or BNB), while the farmers can borrow the currencies to farm with higher APY rates. Win-win.

## Smart Contract Structure

### Bank 🏦 ([code](./contracts/5/Bank.sol))

Bank is the smart contract that manages all leveraged yeild farming positions. All interactions to AlphaHomora happen through this smart contract. If you are a rich wizard 🧙‍♂️, you can deposit your BNB/BNB to earn intersts. If you are a poor farmer 👩‍🌾, you can open a new position on Bank by specifying the debt you will take anda Goblin who will work for your position.

### Goblins 👺 ([code](./contracts/5/Goblin.sol))

### UniswapGoblin 🦄👺 ([code](./contracts/5/UniswapGoblin.sol))

### StrategyAllBNBOnly ⬆️Ξ ([code](./contracts/5/StrategyAllBNBOnly.sol))

### StrategyLiquidate ⬇️Ξ ([code](./contracts/5/StrategyLiquidate.sol))

### Bug Bounty Program: https://immunefi.com/bounty/alphafinance/

## License

[MIT License](https://opensource.org/licenses/MIT)
