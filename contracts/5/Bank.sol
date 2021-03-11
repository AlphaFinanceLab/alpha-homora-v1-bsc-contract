pragma solidity 0.5.16;
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/token/ERC20/ERC20.sol'; // upgradeable
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/math/SafeMath.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.3.0/contracts/math/Math.sol';
import './ReentrancyGuardUpgradeSafe.sol';
import './Initializable.sol';
import './Governable.sol';
import './BankConfig.sol';
import './Goblin.sol';
import './SafeToken.sol';

contract Bank is Initializable, ERC20, ReentrancyGuardUpgradeSafe, Governable {
  /// @notice Libraries
  using SafeToken for address;
  using SafeMath for uint;

  /// @notice Events
  event AddDebt(uint indexed id, uint debtShare);
  event RemoveDebt(uint indexed id, uint debtShare);
  event Work(uint indexed id, uint loan);
  event Kill(uint indexed id, address indexed killer, uint prize, uint left);

  string public name;
  string public symbol;
  uint8 public decimals;

  struct Position {
    address goblin;
    address owner;
    uint debtShare;
  }

  BankConfig public config;
  mapping(uint => Position) public positions;
  uint public nextPositionID;

  uint public glbDebtShare;
  uint public glbDebtVal;
  uint public lastAccrueTime;
  uint public reservePool;

  /// @dev Require that the caller must be an EOA account to avoid flash loans.
  modifier onlyEOA() {
    require(msg.sender == tx.origin, 'not eoa');
    _;
  }

  /// @dev Add more debt to the global debt pool.
  modifier accrue(uint msgValue) {
    if (now > lastAccrueTime) {
      uint interest = pendingInterest(msgValue);
      uint toReserve = interest.mul(config.getReservePoolBps()).div(10000);
      reservePool = reservePool.add(toReserve);
      glbDebtVal = glbDebtVal.add(interest);
      lastAccrueTime = now;
    }
    _;
  }

  function initialize(BankConfig _config) external initializer {
    __Governable__init();
    __ReentrancyGuardUpgradeSafe__init();
    config = _config;
    lastAccrueTime = now;
    nextPositionID = 1;
    name = 'Interest Bearing BNB';
    symbol = 'ibBNB';
    decimals = 18;
  }

  /// @dev Return the pending interest that will be accrued in the next call.
  /// @param msgValue Balance value to subtract off address(this).balance when called from payable functions.
  function pendingInterest(uint msgValue) public view returns (uint) {
    if (now > lastAccrueTime) {
      uint timePast = now.sub(lastAccrueTime);
      uint balance = address(this).balance.sub(msgValue);
      uint ratePerSec = config.getInterestRate(glbDebtVal, balance);
      return ratePerSec.mul(glbDebtVal).mul(timePast).div(1e18);
    } else {
      return 0;
    }
  }

  /// @dev Return the BNB debt value given the debt share. Be careful of unaccrued interests.
  /// @param debtShare The debt share to be converted.
  function debtShareToVal(uint debtShare) public view returns (uint) {
    if (glbDebtShare == 0) return debtShare; // When there's no share, 1 share = 1 val.
    return debtShare.mul(glbDebtVal).div(glbDebtShare);
  }

  /// @dev Return the debt share for the given debt value. Be careful of unaccrued interests.
  /// @param debtVal The debt value to be converted.
  function debtValToShare(uint debtVal) public view returns (uint) {
    if (glbDebtShare == 0) return debtVal; // When there's no share, 1 share = 1 val.
    return debtVal.mul(glbDebtShare).div(glbDebtVal).add(1);
  }

  /// @dev Return BNB value and debt of the given position. Be careful of unaccrued interests.
  /// @param id The position ID to query.
  function positionInfo(uint id) public view returns (uint, uint) {
    Position storage pos = positions[id];
    return (Goblin(pos.goblin).health(id), debtShareToVal(pos.debtShare));
  }

  /// @dev Return the total BNB entitled to the token holders. Be careful of unaccrued interests.
  function totalBNB() public view returns (uint) {
    return address(this).balance.add(glbDebtVal).sub(reservePool);
  }

  /// @dev Add more BNB to the bank. Hope to get some good returns.
  function deposit() external payable accrue(msg.value) nonReentrant {
    uint total = totalBNB().sub(msg.value);
    uint share = total == 0 ? msg.value : msg.value.mul(totalSupply()).div(total);
    _mint(msg.sender, share);
    require(totalSupply() >= 1e17);
  }

  /// @dev Withdraw BNB from the bank by burning the share tokens.
  function withdraw(uint share) external accrue(0) nonReentrant {
    uint amount = share.mul(totalBNB()).div(totalSupply());
    _burn(msg.sender, share);
    SafeToken.safeTransferBNB(msg.sender, amount);
    uint supply = totalSupply();
    require(supply == 0 || supply >= 1e17);
  }

  /// @dev Create a new farming position to unlock your yield farming potential.
  /// @param id The ID of the position to unlock the earning. Use ZERO for new position.
  /// @param goblin The address of the authorized goblin to work for this position.
  /// @param loan The amount of BNB to borrow from the pool.
  /// @param maxReturn The max amount of BNB to return to the pool.
  /// @param data The calldata to pass along to the goblin for more working context.
  function work(
    uint id,
    address goblin,
    uint loan,
    uint maxReturn,
    bytes calldata data
  ) external payable onlyEOA accrue(msg.value) nonReentrant {
    // 1. Sanity check the input position, or add a new position of ID is 0.
    if (id == 0) {
      id = nextPositionID++;
      positions[id].goblin = goblin;
      positions[id].owner = msg.sender;
    } else {
      require(id < nextPositionID, 'bad position id');
      require(positions[id].goblin == goblin, 'bad position goblin');
      require(positions[id].owner == msg.sender, 'not position owner');
    }
    emit Work(id, loan);
    // 2. Make sure the goblin can accept more debt and remove the existing debt.
    require(config.isGoblin(goblin), 'not a goblin');
    require(loan == 0 || config.acceptDebt(goblin), 'goblin not accept more debt');
    uint debt = _removeDebt(id).add(loan);
    // 3. Perform the actual work, using a new scope to avoid stack-too-deep errors.
    uint back;
    {
      uint sendBNB = msg.value.add(loan);
      require(sendBNB <= address(this).balance, 'insufficient BNB in the bank');
      uint beforeBNB = address(this).balance.sub(sendBNB);
      Goblin(goblin).work.value(sendBNB)(id, msg.sender, debt, data);
      back = address(this).balance.sub(beforeBNB);
    }
    // 4. Check and update position debt.
    uint lessDebt = Math.min(debt, Math.min(back, maxReturn));
    debt = debt.sub(lessDebt);
    if (debt > 0) {
      require(debt >= config.minDebtSize(), 'too small debt size');
      uint health = Goblin(goblin).health(id);
      uint workFactor = config.workFactor(goblin, debt);
      require(health.mul(workFactor) >= debt.mul(10000), 'bad work factor');
      _addDebt(id, debt);
    }
    // 5. Return excess BNB back.
    if (back > lessDebt) SafeToken.safeTransferBNB(msg.sender, back - lessDebt);

    // 6. Check total debt share/value not too small
    require(glbDebtShare >= 1e12, 'remaining global debt share too small');
    require(glbDebtVal >= 1e12, 'remaining global debt value too small');
  }

  /// @dev Kill the given to the position. Liquidate it immediately if killFactor condition is met.
  /// @param id The position ID to be killed.
  function kill(uint id) external onlyEOA accrue(0) nonReentrant {
    // 1. Verify that the position is eligible for liquidation.
    Position storage pos = positions[id];
    require(pos.debtShare > 0, 'no debt');
    uint debt = _removeDebt(id);
    uint health = Goblin(pos.goblin).health(id);
    uint killFactor = config.killFactor(pos.goblin, debt);
    require(health.mul(killFactor) < debt.mul(10000), "can't liquidate");
    // 2. Perform liquidation and compute the amount of BNB received.
    uint beforeBNB = address(this).balance;
    Goblin(pos.goblin).liquidate(id);
    uint back = address(this).balance.sub(beforeBNB);
    uint prize = back.mul(config.getKillBps()).div(10000);
    uint rest = back.sub(prize);
    // 3. Clear position debt and return funds to liquidator and position owner.
    if (prize > 0) SafeToken.safeTransferBNB(msg.sender, prize);
    uint left = rest > debt ? rest - debt : 0;
    if (left > 0) SafeToken.safeTransferBNB(pos.owner, left);
    emit Kill(id, msg.sender, prize, left);
  }

  /// @dev Internal function to add the given debt value to the given position.
  function _addDebt(uint id, uint debtVal) internal {
    Position storage pos = positions[id];
    uint debtShare = debtValToShare(debtVal);
    pos.debtShare = pos.debtShare.add(debtShare);
    glbDebtShare = glbDebtShare.add(debtShare);
    glbDebtVal = glbDebtVal.add(debtVal);
    emit AddDebt(id, debtShare);
  }

  /// @dev Internal function to clear the debt of the given position. Return the debt value.
  function _removeDebt(uint id) internal returns (uint) {
    Position storage pos = positions[id];
    uint debtShare = pos.debtShare;
    if (debtShare > 0) {
      uint debtVal = debtShareToVal(debtShare);
      pos.debtShare = 0;
      glbDebtShare = glbDebtShare.sub(debtShare);
      glbDebtVal = glbDebtVal.sub(debtVal);
      emit RemoveDebt(id, debtShare);
      return debtVal;
    } else {
      return 0;
    }
  }

  /// @dev Update bank configuration to a new address. Must only be called by owner.
  /// @param _config The new configurator address.
  function updateConfig(BankConfig _config) external onlyGov {
    config = _config;
  }

  /// @dev Withdraw BNB reserve for underwater positions to the given address.
  /// @param to The address to transfer BNB to.
  /// @param value The number of BNB tokens to withdraw. Must not exceed `reservePool`.
  function withdrawReserve(address to, uint value) external onlyGov nonReentrant {
    reservePool = reservePool.sub(value);
    SafeToken.safeTransferBNB(to, value);
  }

  /// @dev Reduce BNB reserve, effectively giving them to the depositors.
  /// @param value The number of BNB reserve to reduce.
  function reduceReserve(uint value) external onlyGov {
    reservePool = reservePool.sub(value);
  }

  /// @dev Recover ERC20 tokens that were accidentally sent to this smart contract.
  /// @param token The token contract. Can be anything. This contract should not hold ERC20 tokens.
  /// @param to The address to send the tokens to.
  /// @param value The number of tokens to transfer to `to`.
  function recover(
    address token,
    address to,
    uint value
  ) external onlyGov nonReentrant {
    token.safeTransfer(to, value);
  }

  /// @dev Fallback function to accept BNB. Goblins will send BNB back the pool.
  function() external payable {}
}
