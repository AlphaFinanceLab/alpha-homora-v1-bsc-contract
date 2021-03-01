pragma solidity 0.5.16;

import 'openzeppelin-solidity-2.3.0/contracts/token/ERC20/IERC20.sol';

// Making the original MasterChef as an interface leads to compilation fail.
// Use Contract instead of Interface here
contract IMasterChef {
  // Info of each user.
  struct UserInfo {
    uint amount; // How many LP tokens the user has provided.
    uint rewardDebt; // Reward debt. See explanation below.
  }

  // Info of each pool.
  struct PoolInfo {
    IERC20 lpToken; // Address of LP token contract.
    uint allocPoint; // How many allocation points assigned to this pool. SUSHIs to distribute per block.
    uint lastRewardBlock; // Last block number that SUSHIs distribution occurs.
    uint accSushiPerShare; // Accumulated SUSHIs per share, times 1e12. See below.
  }

  address public sushi;

  // Info of each user that stakes LP tokens.
  mapping(uint => PoolInfo) public poolInfo;
  mapping(uint => mapping(address => UserInfo)) public userInfo;

  // Deposit LP tokens to MasterChef for SUSHI allocation.
  function deposit(uint _pid, uint _amount) external {}

  // Withdraw LP tokens from MasterChef.
  function withdraw(uint _pid, uint _amount) external {}
}
