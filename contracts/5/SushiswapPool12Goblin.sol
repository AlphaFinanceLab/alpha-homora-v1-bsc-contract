pragma solidity 0.5.16;
import 'openzeppelin-solidity-2.3.0/contracts/ownership/Ownable.sol';
import 'openzeppelin-solidity-2.3.0/contracts/math/SafeMath.sol';
import 'openzeppelin-solidity-2.3.0/contracts/utils/ReentrancyGuard.sol';
import 'openzeppelin-solidity-2.3.0/contracts/token/ERC20/IERC20.sol';
import '@uniswap/v2-core/contracts/interfaces/IUniswapV2Factory.sol';
import '@uniswap/v2-core/contracts/interfaces/IUniswapV2Pair.sol';
import '@uniswap/v2-core/contracts/libraries/Math.sol';
import './uniswap/IUniswapV2Router02.sol';
import './Strategy.sol';
import './SafeToken.sol';
import './Goblin.sol';
import './interfaces/IMasterChef.sol';

// SushiswapPool12Goblin is specific for SUSHI-ETH pool in Sushiswap.
// In this case, fToken = SUSHI and pid = 12.
contract SushiswapPool12Goblin is Ownable, ReentrancyGuard, Goblin {
  /// @notice Libraries
  using SafeToken for address;
  using SafeMath for uint;

  /// @notice Events
  event Reinvest(address indexed caller, uint reward, uint bounty);
  event AddShare(uint indexed id, uint share);
  event RemoveShare(uint indexed id, uint share);
  event Liquidate(uint indexed id, uint wad);

  /// @notice Immutable variables
  IMasterChef public masterChef;
  IUniswapV2Factory public factory;
  IUniswapV2Router02 public router;
  IUniswapV2Pair public lpToken;
  address public weth;
  address public sushi;
  address public operator;
  uint public constant pid = 12;

  /// @notice Mutable state variables
  mapping(uint => uint) public shares;
  mapping(address => bool) public okStrats;
  uint public totalShare;
  Strategy public addStrat;
  Strategy public liqStrat;
  uint public reinvestBountyBps;

  constructor(
    address _operator,
    IMasterChef _masterChef,
    IUniswapV2Router02 _router,
    Strategy _addStrat,
    Strategy _liqStrat,
    uint _reinvestBountyBps
  ) public {
    operator = _operator;
    weth = _router.WETH();
    masterChef = _masterChef;
    router = _router;
    factory = IUniswapV2Factory(_router.factory());
    (IERC20 _lpToken, , , ) = masterChef.poolInfo(pid);
    lpToken = IUniswapV2Pair(address(_lpToken));
    sushi = address(masterChef.sushi());
    addStrat = _addStrat;
    liqStrat = _liqStrat;
    okStrats[address(addStrat)] = true;
    okStrats[address(liqStrat)] = true;
    reinvestBountyBps = _reinvestBountyBps;
    lpToken.approve(address(_masterChef), uint(-1)); // 100% trust in the staking pool
    lpToken.approve(address(router), uint(-1)); // 100% trust in the router
    sushi.safeApprove(address(router), uint(-1)); // 100% trust in the router
  }

  /// @dev Require that the caller must be an EOA account to avoid flash loans.
  modifier onlyEOA() {
    require(msg.sender == tx.origin, 'not eoa');
    _;
  }

  /// @dev Require that the caller must be the operator (the bank).
  modifier onlyOperator() {
    require(msg.sender == operator, 'not operator');
    _;
  }

  /// @dev Return the entitied LP token balance for the given shares.
  /// @param share The number of shares to be converted to LP balance.
  function shareToBalance(uint share) public view returns (uint) {
    if (totalShare == 0) return share; // When there's no share, 1 share = 1 balance.
    (uint totalBalance, ) = masterChef.userInfo(pid, address(this));
    return share.mul(totalBalance).div(totalShare);
  }

  /// @dev Return the number of shares to receive if staking the given LP tokens.
  /// @param balance the number of LP tokens to be converted to shares.
  function balanceToShare(uint balance) public view returns (uint) {
    if (totalShare == 0) return balance; // When there's no share, 1 share = 1 balance.
    (uint totalBalance, ) = masterChef.userInfo(pid, address(this));
    return balance.mul(totalShare).div(totalBalance);
  }

  /// @dev Re-invest whatever this worker has earned back to staked LP tokens.
  function reinvest() public onlyEOA nonReentrant {
    // 1. Withdraw all the rewards.
    masterChef.withdraw(pid, 0);
    uint reward = sushi.balanceOf(address(this));
    if (reward == 0) return;
    // 2. Send the reward bounty to the caller.
    uint bounty = reward.mul(reinvestBountyBps) / 10000;
    sushi.safeTransfer(msg.sender, bounty);
    // 3. Use add Two-side optimal strategy to convert sushi to ETH and add
    // liquidity to get LP tokens.
    sushi.safeTransfer(address(addStrat), reward.sub(bounty));
    addStrat.execute(address(this), 0, abi.encode(sushi, 0, 0));
    // 4. Mint more LP tokens and stake them for more rewards.
    masterChef.deposit(pid, lpToken.balanceOf(address(this)));
    emit Reinvest(msg.sender, reward, bounty);
  }

  /// @dev Work on the given position. Must be called by the operator.
  /// @param id The position ID to work on.
  /// @param user The original user that is interacting with the operator.
  /// @param debt The amount of user debt to help the strategy make decisions.
  /// @param data The encoded data, consisting of strategy address and calldata.
  function work(
    uint id,
    address user,
    uint debt,
    bytes calldata data
  ) external payable onlyOperator nonReentrant {
    // 1. Convert this position back to LP tokens.
    _removeShare(id);
    // 2. Perform the worker strategy; sending LP tokens + ETH; expecting LP tokens + ETH.
    (address strat, bytes memory ext) = abi.decode(data, (address, bytes));
    require(okStrats[strat], 'unapproved work strategy');
    lpToken.transfer(strat, lpToken.balanceOf(address(this)));
    Strategy(strat).execute.value(msg.value)(user, debt, ext);
    // 3. Add LP tokens back to the farming pool.
    _addShare(id);
    // 4. Return any remaining ETH back to the operator.
    SafeToken.safeTransferETH(msg.sender, address(this).balance);
  }

  /// @dev Return maximum output given the input amount and the status of Uniswap reserves.
  /// @param aIn The amount of asset to market sell.
  /// @param rIn the amount of asset in reserve for input.
  /// @param rOut The amount of asset in reserve for output.
  function getMktSellAmount(
    uint aIn,
    uint rIn,
    uint rOut
  ) public pure returns (uint) {
    if (aIn == 0) return 0;
    require(rIn > 0 && rOut > 0, 'bad reserve values');
    uint aInWithFee = aIn.mul(997);
    uint numerator = aInWithFee.mul(rOut);
    uint denominator = rIn.mul(1000).add(aInWithFee);
    return numerator / denominator;
  }

  /// @dev Return the amount of ETH to receive if we are to liquidate the given position.
  /// @param id The position ID to perform health check.
  function health(uint id) external view returns (uint) {
    // 1. Get the position's LP balance and LP total supply.
    uint lpBalance = shareToBalance(shares[id]);
    uint lpSupply = lpToken.totalSupply(); // Ignore pending mintFee as it is insignificant
    // 2. Get the pool's total supply of WETH and farming token.
    (uint r0, uint r1, ) = lpToken.getReserves();
    (uint totalWETH, uint totalSushi) = lpToken.token0() == weth ? (r0, r1) : (r1, r0);
    // 3. Convert the position's LP tokens to the underlying assets.
    uint userWETH = lpBalance.mul(totalWETH).div(lpSupply);
    uint userSushi = lpBalance.mul(totalSushi).div(lpSupply);
    // 4. Convert all farming tokens to ETH and return total ETH.
    return
      getMktSellAmount(userSushi, totalSushi.sub(userSushi), totalWETH.sub(userWETH)).add(userWETH);
  }

  /// @dev Liquidate the given position by converting it to ETH and return back to caller.
  /// @param id The position ID to perform liquidation
  function liquidate(uint id) external onlyOperator nonReentrant {
    // 1. Convert the position back to LP tokens and use liquidate strategy.
    _removeShare(id);
    lpToken.transfer(address(liqStrat), lpToken.balanceOf(address(this)));
    liqStrat.execute(address(0), 0, abi.encode(sushi, 0));
    // 2. Return all available ETH back to the operator.
    uint wad = address(this).balance;
    SafeToken.safeTransferETH(msg.sender, wad);
    emit Liquidate(id, wad);
  }

  /// @dev Internal function to stake all outstanding LP tokens to the given position ID.
  function _addShare(uint id) internal {
    uint balance = lpToken.balanceOf(address(this));

    if (balance > 0) {
      uint share = balanceToShare(balance);
      masterChef.deposit(pid, balance);
      shares[id] = shares[id].add(share);
      totalShare = totalShare.add(share);
      emit AddShare(id, share);
    }
  }

  /// @dev Internal function to remove shares of the ID and convert to outstanding LP tokens.
  function _removeShare(uint id) internal {
    uint share = shares[id];
    if (share > 0) {
      uint balance = shareToBalance(share);
      masterChef.withdraw(pid, balance);
      totalShare = totalShare.sub(share);
      shares[id] = 0;
      emit RemoveShare(id, share);
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
  ) external onlyOwner nonReentrant {
    token.safeTransfer(to, value);
  }

  /// @dev Set the reward bounty for calling reinvest operations.
  /// @param _reinvestBountyBps The bounty value to update.
  function setReinvestBountyBps(uint _reinvestBountyBps) external onlyOwner {
    reinvestBountyBps = _reinvestBountyBps;
  }

  /// @dev Set the given strategies' approval status.
  /// @param strats The strategy addresses.
  /// @param isOk Whether to approve or unapprove the given strategies.
  function setStrategyOk(address[] calldata strats, bool isOk) external onlyOwner {
    uint len = strats.length;
    for (uint idx = 0; idx < len; idx++) {
      okStrats[strats[idx]] = isOk;
    }
  }

  /// @dev Update critical strategy smart contracts. EMERGENCY ONLY. Bad strategies can steal funds.
  /// @param _addStrat The new add strategy contract.
  /// @param _liqStrat The new liquidate strategy contract.
  function setCriticalStrategies(Strategy _addStrat, Strategy _liqStrat) external onlyOwner {
    addStrat = _addStrat;
    liqStrat = _liqStrat;
  }

  function() external payable {}
}
