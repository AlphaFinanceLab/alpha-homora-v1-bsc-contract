pragma solidity =0.5.16;
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/ownership/Ownable.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/token/ERC20/IERC20.sol';
import 'Uniswap/uniswap-v2-core@1.0.1/contracts/libraries/Math.sol';
import './uniswap/UniswapV2Library.sol';
import './uniswap/IUniswapV2Router02.sol';
import './interfaces/IBank.sol';

// helper methods for interacting with ERC20 tokens and sending BNB that do not consistently return true/false
library TransferHelper {
  function safeApprove(
    address token,
    address to,
    uint value
  ) internal {
    // bytes4(keccak256(bytes('approve(address,uint256)')));
    (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0x095ea7b3, to, value));
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      'TransferHelper: APPROVE_FAILED'
    );
  }

  function safeTransfer(
    address token,
    address to,
    uint value
  ) internal {
    // bytes4(keccak256(bytes('transfer(address,uint256)')));
    (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0xa9059cbb, to, value));
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      'TransferHelper: TRANSFER_FAILED'
    );
  }

  function safeTransferFrom(
    address token,
    address from,
    address to,
    uint value
  ) internal {
    // bytes4(keccak256(bytes('transferFrom(address,address,uint256)')));
    (bool success, bytes memory data) =
      token.call(abi.encodeWithSelector(0x23b872dd, from, to, value));
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      'TransferHelper: TRANSFER_FROM_FAILED'
    );
  }

  function safeTransferBNB(address to, uint value) internal {
    (bool success, ) = to.call.value(value)(new bytes(0));
    require(success, 'TransferHelper: BNB_TRANSFER_FAILED');
  }
}

contract IbBNBRouter is Ownable {
  using SafeMath for uint;

  address public router;
  address public ibBNB;
  address public alpha;
  address public lpToken;

  constructor(
    address _router,
    address _ibBNB,
    address _alpha
  ) public {
    router = _router;
    ibBNB = _ibBNB;
    alpha = _alpha;
    address factory = IUniswapV2Router02(router).factory();
    lpToken = UniswapV2Library.pairFor(factory, ibBNB, alpha);
    IUniswapV2Pair(lpToken).approve(router, uint(-1)); // 100% trust in the router
    IBank(ibBNB).approve(router, uint(-1)); // 100% trust in the router
    IERC20(alpha).approve(router, uint(-1)); // 100% trust in the router
  }

  function() external payable {
    assert(msg.sender == ibBNB); // only accept BNB via fallback from the Bank contract
  }

  // **** BNB-ibBNB FUNCTIONS ****
  // Get number of ibBNB needed to withdraw to get exact amountBNB from the Bank
  function ibBNBForExactBNB(uint amountBNB) public view returns (uint) {
    uint totalBNB = IBank(ibBNB).totalBNB();
    return
      totalBNB == 0
        ? amountBNB
        : amountBNB.mul(IBank(ibBNB).totalSupply()).add(totalBNB).sub(1).div(totalBNB);
  }

  // Add BNB and Alpha from ibBNB-Alpha Pool.
  // 1. Receive BNB and Alpha from caller.
  // 2. Wrap BNB to ibBNB.
  // 3. Provide liquidity to the pool.
  function addLiquidityBNB(
    uint amountAlphaDesired,
    uint amountAlphaMin,
    uint amountBNBMin,
    address to,
    uint deadline
  )
    external
    payable
    returns (
      uint amountAlpha,
      uint amountBNB,
      uint liquidity
    )
  {
    TransferHelper.safeTransferFrom(alpha, msg.sender, address(this), amountAlphaDesired);
    IBank(ibBNB).deposit.value(msg.value)();
    uint amountIbBNBDesired = IBank(ibBNB).balanceOf(address(this));
    uint amountIbBNB;
    (amountAlpha, amountIbBNB, liquidity) = IUniswapV2Router02(router).addLiquidity(
      alpha,
      ibBNB,
      amountAlphaDesired,
      amountIbBNBDesired,
      amountAlphaMin,
      0,
      to,
      deadline
    );
    if (amountAlphaDesired > amountAlpha) {
      TransferHelper.safeTransfer(alpha, msg.sender, amountAlphaDesired.sub(amountAlpha));
    }
    IBank(ibBNB).withdraw(amountIbBNBDesired.sub(amountIbBNB));
    amountBNB = msg.value.sub(address(this).balance);
    if (amountBNB > 0) {
      TransferHelper.safeTransferBNB(msg.sender, address(this).balance);
    }
    require(amountBNB >= amountBNBMin, 'IbBNBRouter: require more BNB than amountBNBmin');
  }

  /// @dev Compute optimal deposit amount
  /// @param amtA amount of token A desired to deposit
  /// @param amtB amount of token B desired to deposit
  /// @param resA amount of token A in reserve
  /// @param resB amount of token B in reserve
  /// (forked from ./StrategyAddTwoSidesOptimal.sol)
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
  /// @param amtB amount of token B desired to deposit
  /// @param resA amount of token A in reserve
  /// @param resB amount of token B in reserve
  /// (forked from ./StrategyAddTwoSidesOptimal.sol)
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

  // Add ibBNB and Alpha to ibBNB-Alpha Pool.
  // All ibBNB and Alpha supplied are optimally swap and add too ibBNB-Alpha Pool.
  function addLiquidityTwoSidesOptimal(
    uint amountIbBNBDesired,
    uint amountAlphaDesired,
    uint amountLPMin,
    address to,
    uint deadline
  ) external returns (uint liquidity) {
    if (amountIbBNBDesired > 0) {
      TransferHelper.safeTransferFrom(ibBNB, msg.sender, address(this), amountIbBNBDesired);
    }
    if (amountAlphaDesired > 0) {
      TransferHelper.safeTransferFrom(alpha, msg.sender, address(this), amountAlphaDesired);
    }
    uint swapAmt;
    bool isReversed;
    {
      (uint r0, uint r1, ) = IUniswapV2Pair(lpToken).getReserves();
      (uint ibBNBReserve, uint alphaReserve) =
        IUniswapV2Pair(lpToken).token0() == ibBNB ? (r0, r1) : (r1, r0);
      (swapAmt, isReversed) = optimalDeposit(
        amountIbBNBDesired,
        amountAlphaDesired,
        ibBNBReserve,
        alphaReserve
      );
    }
    address[] memory path = new address[](2);
    (path[0], path[1]) = isReversed ? (alpha, ibBNB) : (ibBNB, alpha);
    IUniswapV2Router02(router).swapExactTokensForTokens(swapAmt, 0, path, address(this), now);
    (, , liquidity) = IUniswapV2Router02(router).addLiquidity(
      alpha,
      ibBNB,
      IERC20(alpha).balanceOf(address(this)),
      IBank(ibBNB).balanceOf(address(this)),
      0,
      0,
      to,
      deadline
    );
    uint dustAlpha = IERC20(alpha).balanceOf(address(this));
    uint dustIbBNB = IBank(ibBNB).balanceOf(address(this));
    if (dustAlpha > 0) {
      TransferHelper.safeTransfer(alpha, msg.sender, dustAlpha);
    }
    if (dustIbBNB > 0) {
      TransferHelper.safeTransfer(ibBNB, msg.sender, dustIbBNB);
    }
    require(liquidity >= amountLPMin, 'IbBNBRouter: receive less lpToken than amountLPMin');
  }

  // Add BNB and Alpha to ibBNB-Alpha Pool.
  // All BNB and Alpha supplied are optimally swap and add too ibBNB-Alpha Pool.
  function addLiquidityTwoSidesOptimalBNB(
    uint amountAlphaDesired,
    uint amountLPMin,
    address to,
    uint deadline
  ) external payable returns (uint liquidity) {
    if (amountAlphaDesired > 0) {
      TransferHelper.safeTransferFrom(alpha, msg.sender, address(this), amountAlphaDesired);
    }
    IBank(ibBNB).deposit.value(msg.value)();
    uint amountIbBNBDesired = IBank(ibBNB).balanceOf(address(this));
    uint swapAmt;
    bool isReversed;
    {
      (uint r0, uint r1, ) = IUniswapV2Pair(lpToken).getReserves();
      (uint ibBNBReserve, uint alphaReserve) =
        IUniswapV2Pair(lpToken).token0() == ibBNB ? (r0, r1) : (r1, r0);
      (swapAmt, isReversed) = optimalDeposit(
        amountIbBNBDesired,
        amountAlphaDesired,
        ibBNBReserve,
        alphaReserve
      );
    }
    address[] memory path = new address[](2);
    (path[0], path[1]) = isReversed ? (alpha, ibBNB) : (ibBNB, alpha);
    IUniswapV2Router02(router).swapExactTokensForTokens(swapAmt, 0, path, address(this), now);
    (, , liquidity) = IUniswapV2Router02(router).addLiquidity(
      alpha,
      ibBNB,
      IERC20(alpha).balanceOf(address(this)),
      IBank(ibBNB).balanceOf(address(this)),
      0,
      0,
      to,
      deadline
    );
    uint dustAlpha = IERC20(alpha).balanceOf(address(this));
    uint dustIbBNB = IBank(ibBNB).balanceOf(address(this));
    if (dustAlpha > 0) {
      TransferHelper.safeTransfer(alpha, msg.sender, dustAlpha);
    }
    if (dustIbBNB > 0) {
      TransferHelper.safeTransfer(ibBNB, msg.sender, dustIbBNB);
    }
    require(liquidity >= amountLPMin, 'IbBNBRouter: receive less lpToken than amountLPMin');
  }

  // Remove BNB and Alpha from ibBNB-Alpha Pool.
  // 1. Remove ibBNB and Alpha from the pool.
  // 2. Unwrap ibBNB to BNB.
  // 3. Return BNB and Alpha to caller.
  function removeLiquidityBNB(
    uint liquidity,
    uint amountAlphaMin,
    uint amountBNBMin,
    address to,
    uint deadline
  ) public returns (uint amountAlpha, uint amountBNB) {
    TransferHelper.safeTransferFrom(lpToken, msg.sender, address(this), liquidity);
    uint amountIbBNB;
    (amountAlpha, amountIbBNB) = IUniswapV2Router02(router).removeLiquidity(
      alpha,
      ibBNB,
      liquidity,
      amountAlphaMin,
      0,
      address(this),
      deadline
    );
    TransferHelper.safeTransfer(alpha, to, amountAlpha);
    IBank(ibBNB).withdraw(amountIbBNB);
    amountBNB = address(this).balance;
    if (amountBNB > 0) {
      TransferHelper.safeTransferBNB(msg.sender, address(this).balance);
    }
    require(amountBNB >= amountBNBMin, 'IbBNBRouter: receive less BNB than amountBNBmin');
  }

  // Remove liquidity from ibBNB-Alpha Pool and convert all ibBNB to Alpha
  // 1. Remove ibBNB and Alpha from the pool.
  // 2. Swap ibBNB for Alpha.
  // 3. Return Alpha to caller.
  function removeLiquidityAllAlpha(
    uint liquidity,
    uint amountAlphaMin,
    address to,
    uint deadline
  ) public returns (uint amountAlpha) {
    TransferHelper.safeTransferFrom(lpToken, msg.sender, address(this), liquidity);
    (uint removeAmountAlpha, uint removeAmountIbBNB) =
      IUniswapV2Router02(router).removeLiquidity(
        alpha,
        ibBNB,
        liquidity,
        0,
        0,
        address(this),
        deadline
      );
    address[] memory path = new address[](2);
    path[0] = ibBNB;
    path[1] = alpha;
    uint[] memory amounts =
      IUniswapV2Router02(router).swapExactTokensForTokens(removeAmountIbBNB, 0, path, to, deadline);
    TransferHelper.safeTransfer(alpha, to, removeAmountAlpha);
    amountAlpha = removeAmountAlpha.add(amounts[1]);
    require(amountAlpha >= amountAlphaMin, 'IbBNBRouter: receive less Alpha than amountAlphaMin');
  }

  // Swap exact amount of BNB for Token
  // 1. Receive BNB from caller
  // 2. Wrap BNB to ibBNB.
  // 3. Swap ibBNB for Token
  function swapExactBNBForAlpha(
    uint amountAlphaOutMin,
    address to,
    uint deadline
  ) external payable returns (uint[] memory amounts) {
    IBank(ibBNB).deposit.value(msg.value)();
    address[] memory path = new address[](2);
    path[0] = ibBNB;
    path[1] = alpha;
    uint[] memory swapAmounts =
      IUniswapV2Router02(router).swapExactTokensForTokens(
        IBank(ibBNB).balanceOf(address(this)),
        amountAlphaOutMin,
        path,
        to,
        deadline
      );
    amounts = new uint[](2);
    amounts[0] = msg.value;
    amounts[1] = swapAmounts[1];
  }

  // Swap Token for exact amount of BNB
  // 1. Receive Token from caller
  // 2. Swap Token for ibBNB.
  // 3. Unwrap ibBNB to BNB.
  function swapAlphaForExactBNB(
    uint amountBNBOut,
    uint amountAlphaInMax,
    address to,
    uint deadline
  ) external returns (uint[] memory amounts) {
    TransferHelper.safeTransferFrom(alpha, msg.sender, address(this), amountAlphaInMax);
    address[] memory path = new address[](2);
    path[0] = alpha;
    path[1] = ibBNB;
    IBank(ibBNB).withdraw(0);
    uint[] memory swapAmounts =
      IUniswapV2Router02(router).swapTokensForExactTokens(
        ibBNBForExactBNB(amountBNBOut),
        amountAlphaInMax,
        path,
        address(this),
        deadline
      );
    IBank(ibBNB).withdraw(swapAmounts[1]);
    amounts = new uint[](2);
    amounts[0] = swapAmounts[0];
    amounts[1] = address(this).balance;
    TransferHelper.safeTransferBNB(to, address(this).balance);
    if (amountAlphaInMax > amounts[0]) {
      TransferHelper.safeTransfer(alpha, msg.sender, amountAlphaInMax.sub(amounts[0]));
    }
  }

  // Swap exact amount of Token for BNB
  // 1. Receive Token from caller
  // 2. Swap Token for ibBNB.
  // 3. Unwrap ibBNB to BNB.
  function swapExactAlphaForBNB(
    uint amountAlphaIn,
    uint amountBNBOutMin,
    address to,
    uint deadline
  ) external returns (uint[] memory amounts) {
    TransferHelper.safeTransferFrom(alpha, msg.sender, address(this), amountAlphaIn);
    address[] memory path = new address[](2);
    path[0] = alpha;
    path[1] = ibBNB;
    uint[] memory swapAmounts =
      IUniswapV2Router02(router).swapExactTokensForTokens(
        amountAlphaIn,
        0,
        path,
        address(this),
        deadline
      );
    IBank(ibBNB).withdraw(swapAmounts[1]);
    amounts = new uint[](2);
    amounts[0] = swapAmounts[0];
    amounts[1] = address(this).balance;
    TransferHelper.safeTransferBNB(to, amounts[1]);
    require(amounts[1] >= amountBNBOutMin, 'IbBNBRouter: receive less BNB than amountBNBmin');
  }

  // Swap BNB for exact amount of Token
  // 1. Receive BNB from caller
  // 2. Wrap BNB to ibBNB.
  // 3. Swap ibBNB for Token
  function swapBNBForExactAlpha(
    uint amountAlphaOut,
    address to,
    uint deadline
  ) external payable returns (uint[] memory amounts) {
    IBank(ibBNB).deposit.value(msg.value)();
    uint amountIbBNBInMax = IBank(ibBNB).balanceOf(address(this));
    address[] memory path = new address[](2);
    path[0] = ibBNB;
    path[1] = alpha;
    uint[] memory swapAmounts =
      IUniswapV2Router02(router).swapTokensForExactTokens(
        amountAlphaOut,
        amountIbBNBInMax,
        path,
        to,
        deadline
      );
    amounts = new uint[](2);
    amounts[0] = msg.value;
    amounts[1] = swapAmounts[1];
    // Transfer left over BNB back
    if (amountIbBNBInMax > swapAmounts[0]) {
      IBank(ibBNB).withdraw(amountIbBNBInMax.sub(swapAmounts[0]));
      amounts[0] = msg.value.sub(address(this).balance);
      TransferHelper.safeTransferBNB(to, address(this).balance);
    }
  }

  /// @dev Recover ERC20 tokens that were accidentally sent to this smart contract.
  /// @param token The token contract. Can be anything. This contract should not hold ERC20 tokens.
  /// @param to The address to send the tokens to.
  /// @param value The number of tokens to transfer to `to`.
  function recover(
    address token,
    address to,
    uint value
  ) external onlyOwner {
    TransferHelper.safeTransfer(token, to, value);
  }

  /// @dev Recover BNB that were accidentally sent to this smart contract.
  /// @param to The address to send the BNB to.
  /// @param value The number of BNB to transfer to `to`.
  function recoverBNB(address to, uint value) external onlyOwner {
    TransferHelper.safeTransferBNB(to, value);
  }
}
