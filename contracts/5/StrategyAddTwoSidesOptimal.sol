pragma solidity 0.5.16;
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/ownership/Ownable.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/math/SafeMath.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/utils/ReentrancyGuard.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/interfaces/IUniswapV2Factory.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/interfaces/IUniswapV2Pair.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/libraries/Math.sol';
import './uniswap/IUniswapV2Router02.sol';
import './SafeToken.sol';
import './Strategy.sol';

contract StrategyAddTwoSidesOptimal is Ownable, ReentrancyGuard, Strategy {
  using SafeToken for address;
  using SafeMath for uint;

  IUniswapV2Factory public factory;
  IUniswapV2Router02 public router;
  address public wbnb;
  address public goblin;

  /// @dev Create a new add two-side optimal strategy instance.
  /// @param _router The Uniswap router smart contract.
  constructor(IUniswapV2Router02 _router, address _goblin) public {
    factory = IUniswapV2Factory(_router.factory());
    router = _router;
    wbnb = _router.WETH();
    goblin = _goblin;
  }

  /// @dev Throws if called by any account other than the goblin.
  modifier onlyGoblin() {
    require(isGoblin(), 'caller is not the goblin');
    _;
  }

  /// @dev Returns true if the caller is the current goblin.
  function isGoblin() public view returns (bool) {
    return msg.sender == goblin;
  }

  /// @dev Compute optimal deposit amount
  /// @param amtA amount of token A desired to deposit
  /// @param amtB amonut of token B desired to deposit
  /// @param resA amount of token A in reserve
  /// @param resB amount of token B in reserve
  function optimalDeposit(
    uint amtA,
    uint amtB,
    uint resA,
    uint resB
  ) internal pure returns (uint swapAmt, bool isReversed) {
    if (amtA.mul(resB) >= amtB.mul(resA)) {
      swapAmt = _optimalDepositA(amtA, amtB, resA, resB);
      isReversed = false;
    } else {
      swapAmt = _optimalDepositA(amtB, amtA, resB, resA);
      isReversed = true;
    }
  }

  /// @dev Compute optimal deposit amount helper
  /// @param amtA amount of token A desired to deposit
  /// @param amtB amonut of token B desired to deposit
  /// @param resA amount of token A in reserve
  /// @param resB amount of token B in reserve
  function _optimalDepositA(
    uint amtA,
    uint amtB,
    uint resA,
    uint resB
  ) internal pure returns (uint) {
    require(amtA.mul(resB) >= amtB.mul(resA), 'Reversed');

    uint a = 998;
    uint b = uint(1998).mul(resA);
    uint _c = (amtA.mul(resB)).sub(amtB.mul(resA));
    uint c = _c.mul(1000).div(amtB.add(resB)).mul(resA);

    uint d = a.mul(c).mul(4);
    uint e = Math.sqrt(b.mul(b).add(d));

    uint numerator = e.sub(b);
    uint denominator = a.mul(2);

    return numerator.div(denominator);
  }

  /// @dev Execute worker strategy. Take LP tokens + BNB. Return LP tokens + BNB.
  /// @param user User address
  /// @param data Extra calldata information passed along to this strategy.
  function execute(
    address user,
    uint,
    /* debt */
    bytes calldata data
  ) external payable onlyGoblin nonReentrant {
    // 1. Find out what farming token we are dealing with.
    (address fToken, uint fAmount, uint minLPAmount) = abi.decode(data, (address, uint, uint));
    IUniswapV2Pair lpToken = IUniswapV2Pair(factory.getPair(fToken, wbnb));
    // 2. Compute the optimal amount of BNB and fToken to be converted.
    if (fAmount > 0) {
      fToken.safeTransferFrom(user, address(this), fAmount);
    }
    uint ethBalance = address(this).balance;
    uint swapAmt;
    bool isReversed;
    {
      (uint r0, uint r1, ) = lpToken.getReserves();
      (uint ethReserve, uint fReserve) = lpToken.token0() == wbnb ? (r0, r1) : (r1, r0);
      (swapAmt, isReversed) = optimalDeposit(ethBalance, fToken.myBalance(), ethReserve, fReserve);
    }
    // 3. Convert between BNB and farming tokens
    fToken.safeApprove(address(router), 0);
    fToken.safeApprove(address(router), uint(-1));
    address[] memory path = new address[](2);
    (path[0], path[1]) = isReversed ? (fToken, wbnb) : (wbnb, fToken);
    if (isReversed) {
      router.swapExactTokensForETH(swapAmt, 0, path, address(this), now); // farming tokens to BNB
    } else {
      router.swapExactETHForTokens.value(swapAmt)(0, path, address(this), now); // BNB to farming tokens
    }
    // 4. Mint more LP tokens and return all LP tokens to the sender.
    (, , uint moreLPAmount) =
      router.addLiquidityETH.value(address(this).balance)(
        fToken,
        fToken.myBalance(),
        0,
        0,
        address(this),
        now
      );
    require(moreLPAmount >= minLPAmount, 'insufficient LP tokens received');
    lpToken.transfer(msg.sender, lpToken.balanceOf(address(this)));
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
