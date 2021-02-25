chef_address = '0x73feaa1ee314f8c655e354234017be2193c9e24e'
router_address = '0x05ff2b0db69458a0750badebc4f9e13add608c7f'  # pancake router

wbnb_address = '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'

cake_address = '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'
busd_address = '0xe9e7cea3dedca5984780bafc599bd69add087d56'
btcb_address = '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c'
eth_address = '0x2170ed0880ac9a755fd29b2688956bd959f933f8'
usdt_address = '0x55d398326f99059ff775485246999027b3197955'
uni_address = '0xbf5140a22578168fd562dccf235e5d43a02ce9b1'
link_address = '0xf8a0bf9cf54bb92f17374d9e9a321e6a111a51bd'
band_address = '0xad6caeb32cd2c308980a548bd0bc5aa4306c6c18'
yfi_address = '0x88f1a5ae2a3bf98aeaf342d26b30a79438c9142e'
alpha_address = '0xa1faa113cbe53436df28ff0aee54275c13b40975'
ltc_address = '0x4338665cbb7b2485a8855a139b75d5e34ab0db94'
front_address = '0x928e55dab735aa8260af3cedada18b5f70c72f1b'

cake_lp_address = '0xa527a61703d82139f8a06bc30097cc9caa2df5a6'
busd_lp_address = '0x1b96b92314c44b159149f7e0303511fb2fc4774f'
btcb_lp_address = '0x7561eee90e24f3b348e1087a005f78b4c8453524'
eth_lp_address = '0x70d8929d04b60af4fb9b58713ebcf18765ade422'
usdt_lp_address = '0x20bcc3b8a0091ddac2d0bc30f68e6cbb97de59cd'
uni_lp_address = '0x4269e7f43a63cea1ad7707be565a94a9189967e9'
link_lp_address = '0xaebe45e3a03b734c68e5557ae04bfc76917b4686'
band_lp_address = '0xc639187ef82271d8f517de6feae4faf5b517533c'
yfi_lp_address = '0x68ff2ca47d27db5ac0b5c46587645835dd51d3c1'
alpha_lp_address = '0x4e0f3385d932f7179dee045369286ffa6b03d887'
ltc_lp_address = '0xbc765fd113c5bdb2ebc25f711191b56bb8690aec'
front_lp_address = '0x36b7d2e5c7877392fb17f9219efad56f3d794700'

pools = [
  {
    "name":"cake",
    "token":cake_address,
    "lp": cake_lp_address,
    "pid":1,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"busd",
    "token":busd_address,
    "lp": busd_lp_address,
    "pid":2,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"btcb",
    "token":btcb_address,
    "lp": btcb_lp_address,
    "pid":15,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"eth",
    "token":eth_address,
    "lp": eth_lp_address,
    "pid":14,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"usdt",
    "token":usdt_address,
    "lp": usdt_lp_address,
    "pid":17,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"uni",
    "token":uni_address,
    "lp": uni_lp_address,
    "pid":25,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"link",
    "token":link_address,
    "lp": link_lp_address,
    "pid":7,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"band",
    "token":band_address,
    "lp": band_lp_address,
    "pid":4,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"yfi",
    "token":yfi_address,
    "lp": yfi_lp_address,
    "pid":24,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
  {
    "name":"alpha",
    "token":alpha_address,
    "lp": alpha_lp_address,
    "pid":16,
    "goblinConfig":[True, 6250, 7000, 11000]
  },
  {
    "name":"ltc",
    "token":ltc_address,
    "lp": ltc_lp_address,
    "pid":54,
    "goblinConfig":[True, 5500, 6000, 11000]
  },
  {
    "name":"front",
    "token":front_address,
    "lp": front_lp_address,
    "pid":57,
    "goblinConfig":[True, 7250, 8000, 11000]
  },
]