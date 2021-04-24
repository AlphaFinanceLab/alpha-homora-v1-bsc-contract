pragma solidity 0.5.16;

interface IAny {
  function name() external view returns (string memory);

  function owner() external view returns (address);

  function issue(uint) external;

  function issue(address, uint) external;

  function mint(address, uint) external;

  function transfer(address, uint) external;

  function transferFrom(
    address,
    address,
    uint
  ) external;

  function approve(address, uint) external;

  function lpToken() external view returns (address);

  function mint(
    address,
    uint,
    uint
  ) external returns (bool);

  function configureMinter(address, uint) external returns (bool);

  function masterMinter() external view returns (address);

  function deposit() external payable;

  function deposit(uint) external;

  function decimals() external view returns (uint);

  function target() external view returns (address);

  function erc20Impl() external view returns (address);

  function custodian() external view returns (address);

  function requestPrint(address, uint) external returns (bytes32);

  function confirmPrint(bytes32) external;

  function invest(uint) external;

  function increaseSupply(uint) external;

  function supplyController() external view returns (address);

  function getModules() external view returns (address[] memory);

  function addMinter(address) external;

  function governance() external view returns (address);

  function core() external view returns (address);

  function factory() external view returns (address);

  function token0() external view returns (address);

  function token1() external view returns (address);

  function getReserves()
    external
    view
    returns (
      uint,
      uint,
      uint
    );

  function createPair(address, address) external returns (address);

  function getPair(address, address) external view returns (address);

  function totalSupply() external view returns (uint);

  function balanceOf(address) external view returns (uint);

  function symbol() external view returns (string memory);

  function getFinalTokens() external view returns (address[] memory);

  function joinPool(uint, uint[] calldata) external;

  function getBalance(address) external view returns (uint);

  function createTokens(uint) external returns (bool);

  function resolverAddressesRequired() external view returns (bytes32[] memory addresses);

  function exchangeRateStored() external view returns (uint);

  function accrueInterest() external returns (uint);

  function resolver() external view returns (address);

  function repository(bytes32) external view returns (address);

  function underlying() external view returns (address);

  function mint(uint) external returns (uint);

  function redeem(uint) external returns (uint);

  function minter() external view returns (address);

  function borrow(uint) external returns (uint);

  function work(
    uint,
    address,
    uint,
    uint,
    bytes calldata
  ) external;

  function execute(
    address,
    uint,
    bytes calldata
  ) external;

  function addLiquidity(
    address,
    address,
    uint,
    uint,
    uint,
    uint,
    address,
    uint
  )
    external
    returns (
      uint,
      uint,
      uint
    );

  function addLiquidityETH(
    address token,
    uint amountTokenDesired,
    uint amountTokenMin,
    uint amountETHMin,
    address to,
    uint deadline
  )
    external
    payable
    returns (
      uint amountToken,
      uint amountETH,
      uint liquidity
    );

  function positionInfo(uint) external view returns (uint, uint);

  function withdraw(uint) external;

  function reinvest() external;

  function nextPositionID() external view returns (uint);

  function poolInfo(uint)
    external
    view
    returns (
      address,
      uint,
      uint,
      uint
    );

  function add(
    uint,
    address,
    bool
  ) external;

  function sync() external;

  function swapExactETHForTokens(
    uint,
    address[] calldata,
    address,
    uint
  ) external returns (uint[] memory);

  function getOwner() external view returns (address);
}
