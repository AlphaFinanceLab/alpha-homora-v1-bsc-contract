pragma solidity 0.5.16;

interface Goblin {
  /// @dev Work on a (potentially new) position. Optionally send ETH back to Bank.
  function work(
    uint id,
    address user,
    uint debt,
    bytes calldata data
  ) external payable;

  /// @dev Re-invest whatever the goblin is working on.
  function reinvest() external;

  /// @dev Return the amount of ETH wei to get back if we are to liquidate the position.
  function health(uint id) external view returns (uint);

  /// @dev Liquidate the given position to ETH. Send all ETH back to Bank.
  function liquidate(uint id) external;
}
