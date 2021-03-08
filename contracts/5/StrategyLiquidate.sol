pragma solidity 0.5.16;
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/ownership/Ownable.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/utils/ReentrancyGuard.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/interfaces/IUniswapV2Factory.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/interfaces/IUniswapV2Pair.sol';
import './uniswap/IUniswapV2Router02.sol';
import './SafeToken.sol';
import './Strategy.sol';

contract StrategyLiquidate is Ownable, ReentrancyGuard, Strategy {
  using SafeToken for address;

  IUniswapV2Factory public factory;
  IUniswapV2Router02 public router;
  address public wbnb;

  /// @dev Create a new liquidate strategy instance.
  /// @param _router The Uniswap router smart contract.
  constructor(IUniswapV2Router02 _router) public {
    factory = IUniswapV2Factory(_router.factory());
    router = _router;
    wbnb = _router.WETH();
  }

  /// @dev Execute worker strategy. Take LP tokens. Return BNB.
  /// @param data Extra calldata information passed along to this strategy.
  function execute(
    address, /* user */
    uint, /* debt */
    bytes calldata data
  ) external payable nonReentrant {
    // 1. Find out what farming token we are dealing with.
    (address fToken, uint minBNB) = abi.decode(data, (address, uint));
    IUniswapV2Pair lpToken = IUniswapV2Pair(factory.getPair(fToken, wbnb));
    // 2. Remove all liquidity back to BNB and farming tokens.
    lpToken.approve(address(router), uint(-1));
    router.removeLiquidityETH(fToken, lpToken.balanceOf(address(this)), 0, 0, address(this), now);
    // 3. Convert farming tokens to BNB.
    address[] memory path = new address[](2);
    path[0] = fToken;
    path[1] = wbnb;
    fToken.safeApprove(address(router), 0);
    fToken.safeApprove(address(router), uint(-1));
    router.swapExactTokensForETH(fToken.myBalance(), 0, path, address(this), now);
    // 4. Return all BNB back to the original caller.
    uint balance = address(this).balance;
    require(balance >= minBNB, 'insufficient BNB received');
    SafeToken.safeTransferBNB(msg.sender, balance);
  }

  /// @dev Recover ERC20 tokens that were accidentally sent to this smart contract.
  /// @param token The token contract. Can be anything. This contract should not hold ERC20 tokens.
  /// @param to The address to send the tokens to.
  /// @param value The number of tokens to transfer to `to`.
  function recover(
    address token,
    address to,
    uint value
  ) external onlyOwner nonReentrant {
    token.safeTransfer(to, value);
  }

  function() external payable {}
}
