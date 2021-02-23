pragma solidity =0.5.16;

import 'Uniswap/uniswap-v2-core@1.0.1/contracts/interfaces/IUniswapV2Factory.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/token/ERC20/IERC20.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/math/SafeMath.sol';

import '../wbnb/IWBNB.sol';
import './UniswapV2Library.sol';
import './IUniswapV2Router02.sol';

// helper methods for interacting with ERC20 tokens and sending BNB that do not consistently return true/false
library TransferHelper1 {
  function safeApprove(
    address token,
    address to,
    uint value
  ) internal {
    // bytes4(keccak256(bytes('approve(address,uint256)')));
    (bool success, bytes memory data) = token.call(abi.encodeWithSelector(0x095ea7b3, to, value));
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      'TransferHelper1: APPROVE_FAILED'
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
      'TransferHelper1: TRANSFER_FAILED'
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
      'TransferHelper1: TRANSFER_FROM_FAILED'
    );
  }

  function safeTransferBNB(address to, uint value) internal {
    (bool success, ) = to.call.value(value)(new bytes(0));
    require(success, 'TransferHelper1: BNB_TRANSFER_FAILED');
  }
}

contract UniswapV2Router02 is IUniswapV2Router02 {
  using SafeMath for uint;

  address public factory;
  address public WBNB;

  modifier ensure(uint deadline) {
    require(deadline >= block.timestamp, 'UniswapV2Router: EXPIRED');
    _;
  }

  constructor(address _factory, address _WBNB) public {
    factory = _factory;
    WBNB = _WBNB;
  }

  function() external payable {
    assert(msg.sender == WBNB); // only accept BNB via fallback from the WBNB contract
  }

  // **** ADD LIQUIDITY ****
  function _addLiquidity(
    address tokenA,
    address tokenB,
    uint amountADesired,
    uint amountBDesired,
    uint amountAMin,
    uint amountBMin
  ) internal returns (uint amountA, uint amountB) {
    // create the pair if it doesn't exist yet
    if (IUniswapV2Factory(factory).getPair(tokenA, tokenB) == address(0)) {
      IUniswapV2Factory(factory).createPair(tokenA, tokenB);
    }
    (uint reserveA, uint reserveB) = UniswapV2Library.getReserves(factory, tokenA, tokenB);
    if (reserveA == 0 && reserveB == 0) {
      (amountA, amountB) = (amountADesired, amountBDesired);
    } else {
      uint amountBOptimal = UniswapV2Library.quote(amountADesired, reserveA, reserveB);
      if (amountBOptimal <= amountBDesired) {
        require(amountBOptimal >= amountBMin, 'UniswapV2Router: INSUFFICIENT_B_AMOUNT');
        (amountA, amountB) = (amountADesired, amountBOptimal);
      } else {
        uint amountAOptimal = UniswapV2Library.quote(amountBDesired, reserveB, reserveA);
        assert(amountAOptimal <= amountADesired);
        require(amountAOptimal >= amountAMin, 'UniswapV2Router: INSUFFICIENT_A_AMOUNT');
        (amountA, amountB) = (amountAOptimal, amountBDesired);
      }
    }
  }

  function addLiquidity(
    address tokenA,
    address tokenB,
    uint amountADesired,
    uint amountBDesired,
    uint amountAMin,
    uint amountBMin,
    address to,
    uint deadline
  )
    external
    ensure(deadline)
    returns (
      uint amountA,
      uint amountB,
      uint liquidity
    )
  {
    (amountA, amountB) = _addLiquidity(
      tokenA,
      tokenB,
      amountADesired,
      amountBDesired,
      amountAMin,
      amountBMin
    );
    address pair = UniswapV2Library.pairFor(factory, tokenA, tokenB);
    TransferHelper1.safeTransferFrom(tokenA, msg.sender, pair, amountA);
    TransferHelper1.safeTransferFrom(tokenB, msg.sender, pair, amountB);
    liquidity = IUniswapV2Pair(pair).mint(to);
  }

  function addLiquidityBNB(
    address token,
    uint amountTokenDesired,
    uint amountTokenMin,
    uint amountBNBMin,
    address to,
    uint deadline
  )
    external
    payable
    ensure(deadline)
    returns (
      uint amountToken,
      uint amountBNB,
      uint liquidity
    )
  {
    (amountToken, amountBNB) = _addLiquidity(
      token,
      WBNB,
      amountTokenDesired,
      msg.value,
      amountTokenMin,
      amountBNBMin
    );
    address pair = UniswapV2Library.pairFor(factory, token, WBNB);
    TransferHelper1.safeTransferFrom(token, msg.sender, pair, amountToken);
    IWBNB(WBNB).deposit.value(amountBNB)();
    assert(IWBNB(WBNB).transfer(pair, amountBNB));
    liquidity = IUniswapV2Pair(pair).mint(to);
    // refund dust eth, if any
    if (msg.value > amountBNB) TransferHelper1.safeTransferBNB(msg.sender, msg.value - amountBNB);
  }

  // **** REMOVE LIQUIDITY ****
  function removeLiquidity(
    address tokenA,
    address tokenB,
    uint liquidity,
    uint amountAMin,
    uint amountBMin,
    address to,
    uint deadline
  ) public ensure(deadline) returns (uint amountA, uint amountB) {
    address pair = UniswapV2Library.pairFor(factory, tokenA, tokenB);
    IUniswapV2Pair(pair).transferFrom(msg.sender, pair, liquidity); // send liquidity to pair
    (uint amount0, uint amount1) = IUniswapV2Pair(pair).burn(to);
    (address token0, ) = UniswapV2Library.sortTokens(tokenA, tokenB);
    (amountA, amountB) = tokenA == token0 ? (amount0, amount1) : (amount1, amount0);
    require(amountA >= amountAMin, 'UniswapV2Router: INSUFFICIENT_A_AMOUNT');
    require(amountB >= amountBMin, 'UniswapV2Router: INSUFFICIENT_B_AMOUNT');
  }

  function removeLiquidityBNB(
    address token,
    uint liquidity,
    uint amountTokenMin,
    uint amountBNBMin,
    address to,
    uint deadline
  ) public ensure(deadline) returns (uint amountToken, uint amountBNB) {
    (amountToken, amountBNB) = removeLiquidity(
      token,
      WBNB,
      liquidity,
      amountTokenMin,
      amountBNBMin,
      address(this),
      deadline
    );
    TransferHelper1.safeTransfer(token, to, amountToken);
    IWBNB(WBNB).withdraw(amountBNB);
    TransferHelper1.safeTransferBNB(to, amountBNB);
  }

  function removeLiquidityWithPermit(
    address tokenA,
    address tokenB,
    uint liquidity,
    uint amountAMin,
    uint amountBMin,
    address to,
    uint deadline,
    bool approveMax,
    uint8 v,
    bytes32 r,
    bytes32 s
  ) external returns (uint amountA, uint amountB) {
    address pair = UniswapV2Library.pairFor(factory, tokenA, tokenB);
    uint value = approveMax ? uint(-1) : liquidity;
    IUniswapV2Pair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
    (amountA, amountB) = removeLiquidity(
      tokenA,
      tokenB,
      liquidity,
      amountAMin,
      amountBMin,
      to,
      deadline
    );
  }

  function removeLiquidityBNBWithPermit(
    address token,
    uint liquidity,
    uint amountTokenMin,
    uint amountBNBMin,
    address to,
    uint deadline,
    bool approveMax,
    uint8 v,
    bytes32 r,
    bytes32 s
  ) external returns (uint amountToken, uint amountBNB) {
    address pair = UniswapV2Library.pairFor(factory, token, WBNB);
    uint value = approveMax ? uint(-1) : liquidity;
    IUniswapV2Pair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
    (amountToken, amountBNB) = removeLiquidityBNB(
      token,
      liquidity,
      amountTokenMin,
      amountBNBMin,
      to,
      deadline
    );
  }

  // **** REMOVE LIQUIDITY (supporting fee-on-transfer tokens) ****
  function removeLiquidityBNBSupportingFeeOnTransferTokens(
    address token,
    uint liquidity,
    uint amountTokenMin,
    uint amountBNBMin,
    address to,
    uint deadline
  ) public ensure(deadline) returns (uint amountBNB) {
    (, amountBNB) = removeLiquidity(
      token,
      WBNB,
      liquidity,
      amountTokenMin,
      amountBNBMin,
      address(this),
      deadline
    );
    TransferHelper1.safeTransfer(token, to, IERC20(token).balanceOf(address(this)));
    IWBNB(WBNB).withdraw(amountBNB);
    TransferHelper1.safeTransferBNB(to, amountBNB);
  }

  function removeLiquidityBNBWithPermitSupportingFeeOnTransferTokens(
    address token,
    uint liquidity,
    uint amountTokenMin,
    uint amountBNBMin,
    address to,
    uint deadline,
    bool approveMax,
    uint8 v,
    bytes32 r,
    bytes32 s
  ) external returns (uint amountBNB) {
    address pair = UniswapV2Library.pairFor(factory, token, WBNB);
    uint value = approveMax ? uint(-1) : liquidity;
    IUniswapV2Pair(pair).permit(msg.sender, address(this), value, deadline, v, r, s);
    amountBNB = removeLiquidityBNBSupportingFeeOnTransferTokens(
      token,
      liquidity,
      amountTokenMin,
      amountBNBMin,
      to,
      deadline
    );
  }

  // **** SWAP ****
  // requires the initial amount to have already been sent to the first pair
  function _swap(
    uint[] memory amounts,
    address[] memory path,
    address _to
  ) internal {
    for (uint i; i < path.length - 1; i++) {
      (address input, address output) = (path[i], path[i + 1]);
      (address token0, ) = UniswapV2Library.sortTokens(input, output);
      uint amountOut = amounts[i + 1];
      (uint amount0Out, uint amount1Out) =
        input == token0 ? (uint(0), amountOut) : (amountOut, uint(0));
      address to =
        i < path.length - 2 ? UniswapV2Library.pairFor(factory, output, path[i + 2]) : _to;
      IUniswapV2Pair(UniswapV2Library.pairFor(factory, input, output)).swap(
        amount0Out,
        amount1Out,
        to,
        new bytes(0)
      );
    }
  }

  function swapExactTokensForTokens(
    uint amountIn,
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) returns (uint[] memory amounts) {
    amounts = UniswapV2Library.getAmountsOut(factory, amountIn, path);
    require(
      amounts[amounts.length - 1] >= amountOutMin,
      'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'
    );
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amounts[0]
    );
    _swap(amounts, path, to);
  }

  function swapTokensForExactTokens(
    uint amountOut,
    uint amountInMax,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) returns (uint[] memory amounts) {
    amounts = UniswapV2Library.getAmountsIn(factory, amountOut, path);
    require(amounts[0] <= amountInMax, 'UniswapV2Router: EXCESSIVE_INPUT_AMOUNT');
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amounts[0]
    );
    _swap(amounts, path, to);
  }

  function swapExactBNBForTokens(
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external payable ensure(deadline) returns (uint[] memory amounts) {
    require(path[0] == WBNB, 'UniswapV2Router: INVALID_PATH');
    amounts = UniswapV2Library.getAmountsOut(factory, msg.value, path);
    require(
      amounts[amounts.length - 1] >= amountOutMin,
      'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'
    );
    IWBNB(WBNB).deposit.value(amounts[0])();
    assert(IWBNB(WBNB).transfer(UniswapV2Library.pairFor(factory, path[0], path[1]), amounts[0]));
    _swap(amounts, path, to);
  }

  function swapTokensForExactBNB(
    uint amountOut,
    uint amountInMax,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) returns (uint[] memory amounts) {
    require(path[path.length - 1] == WBNB, 'UniswapV2Router: INVALID_PATH');
    amounts = UniswapV2Library.getAmountsIn(factory, amountOut, path);
    require(amounts[0] <= amountInMax, 'UniswapV2Router: EXCESSIVE_INPUT_AMOUNT');
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amounts[0]
    );
    _swap(amounts, path, address(this));
    IWBNB(WBNB).withdraw(amounts[amounts.length - 1]);
    TransferHelper1.safeTransferBNB(to, amounts[amounts.length - 1]);
  }

  function swapExactTokensForBNB(
    uint amountIn,
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) returns (uint[] memory amounts) {
    require(path[path.length - 1] == WBNB, 'UniswapV2Router: INVALID_PATH');
    amounts = UniswapV2Library.getAmountsOut(factory, amountIn, path);
    require(
      amounts[amounts.length - 1] >= amountOutMin,
      'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'
    );
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amounts[0]
    );
    _swap(amounts, path, address(this));
    IWBNB(WBNB).withdraw(amounts[amounts.length - 1]);
    TransferHelper1.safeTransferBNB(to, amounts[amounts.length - 1]);
  }

  function swapBNBForExactTokens(
    uint amountOut,
    address[] calldata path,
    address to,
    uint deadline
  ) external payable ensure(deadline) returns (uint[] memory amounts) {
    require(path[0] == WBNB, 'UniswapV2Router: INVALID_PATH');
    amounts = UniswapV2Library.getAmountsIn(factory, amountOut, path);
    require(amounts[0] <= msg.value, 'UniswapV2Router: EXCESSIVE_INPUT_AMOUNT');
    IWBNB(WBNB).deposit.value(amounts[0])();
    assert(IWBNB(WBNB).transfer(UniswapV2Library.pairFor(factory, path[0], path[1]), amounts[0]));
    _swap(amounts, path, to);
    // refund dust eth, if any
    if (msg.value > amounts[0]) TransferHelper1.safeTransferBNB(msg.sender, msg.value - amounts[0]);
  }

  // **** SWAP (supporting fee-on-transfer tokens) ****
  // requires the initial amount to have already been sent to the first pair
  function _swapSupportingFeeOnTransferTokens(address[] memory path, address _to) internal {
    for (uint i; i < path.length - 1; i++) {
      (address input, address output) = (path[i], path[i + 1]);
      (address token0, ) = UniswapV2Library.sortTokens(input, output);
      IUniswapV2Pair pair = IUniswapV2Pair(UniswapV2Library.pairFor(factory, input, output));
      uint amountInput;
      uint amountOutput;
      {
        // scope to avoid stack too deep errors
        (uint reserve0, uint reserve1, ) = pair.getReserves();
        (uint reserveInput, uint reserveOutput) =
          input == token0 ? (reserve0, reserve1) : (reserve1, reserve0);
        amountInput = IERC20(input).balanceOf(address(pair)).sub(reserveInput);
        amountOutput = UniswapV2Library.getAmountOut(amountInput, reserveInput, reserveOutput);
      }
      (uint amount0Out, uint amount1Out) =
        input == token0 ? (uint(0), amountOutput) : (amountOutput, uint(0));
      address to =
        i < path.length - 2 ? UniswapV2Library.pairFor(factory, output, path[i + 2]) : _to;
      pair.swap(amount0Out, amount1Out, to, new bytes(0));
    }
  }

  function swapExactTokensForTokensSupportingFeeOnTransferTokens(
    uint amountIn,
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) {
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amountIn
    );
    uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
    _swapSupportingFeeOnTransferTokens(path, to);
    require(
      IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
      'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'
    );
  }

  function swapExactBNBForTokensSupportingFeeOnTransferTokens(
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external payable ensure(deadline) {
    require(path[0] == WBNB, 'UniswapV2Router: INVALID_PATH');
    uint amountIn = msg.value;
    IWBNB(WBNB).deposit.value(amountIn)();
    assert(IWBNB(WBNB).transfer(UniswapV2Library.pairFor(factory, path[0], path[1]), amountIn));
    uint balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
    _swapSupportingFeeOnTransferTokens(path, to);
    require(
      IERC20(path[path.length - 1]).balanceOf(to).sub(balanceBefore) >= amountOutMin,
      'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT'
    );
  }

  function swapExactTokensForBNBSupportingFeeOnTransferTokens(
    uint amountIn,
    uint amountOutMin,
    address[] calldata path,
    address to,
    uint deadline
  ) external ensure(deadline) {
    require(path[path.length - 1] == WBNB, 'UniswapV2Router: INVALID_PATH');
    TransferHelper1.safeTransferFrom(
      path[0],
      msg.sender,
      UniswapV2Library.pairFor(factory, path[0], path[1]),
      amountIn
    );
    _swapSupportingFeeOnTransferTokens(path, address(this));
    uint amountOut = IERC20(WBNB).balanceOf(address(this));
    require(amountOut >= amountOutMin, 'UniswapV2Router: INSUFFICIENT_OUTPUT_AMOUNT');
    IWBNB(WBNB).withdraw(amountOut);
    TransferHelper1.safeTransferBNB(to, amountOut);
  }

  // **** LIBRARY FUNCTIONS ****
  function quote(
    uint amountA,
    uint reserveA,
    uint reserveB
  ) public pure returns (uint amountB) {
    return UniswapV2Library.quote(amountA, reserveA, reserveB);
  }

  function getAmountOut(
    uint amountIn,
    uint reserveIn,
    uint reserveOut
  ) public pure returns (uint amountOut) {
    return UniswapV2Library.getAmountOut(amountIn, reserveIn, reserveOut);
  }

  function getAmountIn(
    uint amountOut,
    uint reserveIn,
    uint reserveOut
  ) public pure returns (uint amountIn) {
    return UniswapV2Library.getAmountIn(amountOut, reserveIn, reserveOut);
  }

  function getAmountsOut(uint amountIn, address[] memory path)
    public
    view
    returns (uint[] memory amounts)
  {
    return UniswapV2Library.getAmountsOut(factory, amountIn, path);
  }

  function getAmountsIn(uint amountOut, address[] memory path)
    public
    view
    returns (uint[] memory amounts)
  {
    return UniswapV2Library.getAmountsIn(factory, amountOut, path);
  }
}
