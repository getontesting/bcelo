# Submission — Celo Corridor Agent

Event: **Agents Open for Business** (Loops House) · Celo mainnet (42220)
Project: `https://github.com/getontesting/bcelo`
Attribution tag (assigned by platform): **`celo_69fe50f9aa63`**
ERC-8004 agentId: **10077** · agent wallet: `0x2Ff10a4748902E82E82835Edef6d98c306e4ba38`
Payout wallet: `0x2Ff10a4748902E82E82835Edef6d98c306e4ba38`
X post: `https://x.com/CryptoBits03/status/2123859111054029181`

## Track 1 — Stablecoin Corridors (Textile FX)
Named user: **M RIFKI TRI ADITYA**, Jl Sinyal Gunung Gajah, freelance web3 developer
and airdrop enthusiast. Recipient wallet (outside team, not pre-funded):
`0x6cd38eddeb7c0972a93056e20b8e1b11eb141eef`.

Three rounds, each approval + swap + payout, all tagged `celo_69fe50f9aa63`:

| Corridor | Swap tx | Payout tx |
|---|---|---|
| USDT → IDRX | `0xfadc5702d58a64c048b56316ad7731692305bd951544517479815833e2b2f955` | `0x85c03b3ad8ca8f72e0bc94ad0eb3c60a518efe238ae76e5f4f5ec11268520474` |
| USDT → cNGN | `0xf127380e1ced32795356a7a790ec02189f46c05f5464ed178ade8b821aca9bf5` | `0xbf43879aa64748a5e618815cf3c3ed4461936eaa83653212da3806c08ebdb938` |
| USDT → IDRX | `0x6f2b41dba7ff712c4c0b985c7b4447533afaf638c932add92bb6412cac3ba59d` | `0xcce959b492afc755fa1b66f2b9f3516c2ed5b39b4b3f88728def4164b997cb30` |

Approval txs: `0xc61631e1...`, `0x048a9864...`, `0xf1c545ca...`
Verify any tag with: `python -m src.cli verify <tx>`

## Track 2 — Agent Vault + x402
- Agent Vault MCP signed in to `https://github.com/login` with mock tokens only;
  `fill_login` = `filled=2/2`, `observe_page` = `accountControl; looks signed in`.
  The agent never saw the real password.
- x402 payment: `0xf72b3bf1d7a6ce96b2c29b9b0dafb528ba0c5b0db8e425a6a9aba6f0eb29cd1e`
  (block 83290930), $0.10 USDT via the hosted Celo facilitator.
- Spend controls: $1/payment cap; test card only, no real card checkout.
- Public X post with @selfxyz @Celo and demo clip: see link above.

## Track 4 — Altana Agent Wallets
- Passkey smart wallet: `0xBf39b7f2211128b5148d45eA28b4052349d2aBe0`
- Activation tx: `0x36f126e4a9f23aec7d7f96c9b48b477641efe25d7bbab26c4ca63a45cf163384`
  (block 83294878, success)
- Session key in Keystore: `0xffa9945f8e0c23a9abb9a33b015858d0cedd1ee0fe2bc13d341e0b9e83985eaf`
- Policy: spend cap 0.001 CELO/day, contract allowlist = the wallet itself,
  expiry 1 hour, revocable in one transaction.
- Product review: `https://github.com/getontesting/bcelo/issues/1`
- Note: revoke transaction was not obtainable — WebAuthn prompt did not resolve
  in this environment. Wallet + session + policy are verified on-chain.

## Track 3 — Self Agent ID
Not entered: no supported passport document available.

## Reproduce
```bash
pip install -r requirements.txt
cd sidecars && npm install && cd ..
python -m src.cli onboarding
python -m src.cli verify 0xfadc5702d58a64c048b56316ad7731692305bd951544517479815833e2b2f955
```
