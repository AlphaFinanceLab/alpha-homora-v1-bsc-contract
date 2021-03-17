pragma solidity 0.5.16;
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/ownership/Ownable.sol';
import './BankConfig.sol';

contract SimpleBankConfig is BankConfig, Ownable {
  /// @notice Configuration for each goblin.
  struct GoblinConfig {
    bool isGoblin;
    bool acceptDebt;
    uint workFactor;
    uint killFactor;
  }

  /// The minimum BNB debt size per position.
  uint public minDebtSize;
  /// The interest rate per second, multiplied by 1e18.
  uint public interestRate;
  /// The portion of interests allocated to the reserve pool.
  uint public getReservePoolBps;
  /// The reward for successfully killing a position.
  uint public getKillBps;
  /// Mapping for goblin address to its configuration.
  mapping(address => GoblinConfig) public goblins;

  constructor(
    uint _minDebtSize,
    uint _interestRate,
    uint _reservePoolBps,
    uint _killBps
  ) public {
    setParams(_minDebtSize, _interestRate, _reservePoolBps, _killBps);
  }

  /// @dev Set all the basic parameters. Must only be called by the owner.
  /// @param _minDebtSize The new minimum debt size value.
  /// @param _interestRate The new interest rate per second value.
  /// @param _reservePoolBps The new interests allocated to the reserve pool value.
  /// @param _killBps The new reward for killing a position value.
  function setParams(
    uint _minDebtSize,
    uint _interestRate,
    uint _reservePoolBps,
    uint _killBps
  ) public onlyOwner {
    minDebtSize = _minDebtSize;
    interestRate = _interestRate;
    getReservePoolBps = _reservePoolBps;
    getKillBps = _killBps;
  }

  /// @dev Set the configuration for the given goblin. Must only be called by the owner.
  /// @param goblin The goblin address to set configuration.
  /// @param _isGoblin Whether the given address is a valid goblin.
  /// @param _acceptDebt Whether the goblin is accepting new debts.
  /// @param _workFactor The work factor value for this goblin.
  /// @param _killFactor The kill factor value for this goblin.
  function setGoblin(
    address goblin,
    bool _isGoblin,
    bool _acceptDebt,
    uint _workFactor,
    uint _killFactor
  ) public onlyOwner {
    goblins[goblin] = GoblinConfig({
      isGoblin: _isGoblin,
      acceptDebt: _acceptDebt,
      workFactor: _workFactor,
      killFactor: _killFactor
    });
  }

  /// @dev Return the interest rate per second, using 1e18 as denom.
  function getInterestRate(
    uint, /* debt */
    uint /* floating */
  ) external view returns (uint) {
    return interestRate;
  }

  /// @dev Return whether the given address is a goblin.
  function isGoblin(address goblin) external view returns (bool) {
    return goblins[goblin].isGoblin;
  }

  /// @dev Return whether the given goblin accepts more debt. Revert on non-goblin.
  function acceptDebt(address goblin) external view returns (bool) {
    require(goblins[goblin].isGoblin, '!goblin');
    return goblins[goblin].acceptDebt;
  }

  /// @dev Return the work factor for the goblin + BNB debt, using 1e4 as denom. Revert on non-goblin.
  function workFactor(
    address goblin,
    uint /* debt */
  ) external view returns (uint) {
    require(goblins[goblin].isGoblin, '!goblin');
    return goblins[goblin].workFactor;
  }

  /// @dev Return the kill factor for the goblin + BNB debt, using 1e4 as denom. Revert on non-goblin.
  function killFactor(
    address goblin,
    uint /* debt */
  ) external view returns (uint) {
    require(goblins[goblin].isGoblin, '!goblin');
    return goblins[goblin].killFactor;
  }
}
