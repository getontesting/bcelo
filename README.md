# Agents Open for Business — entry (Celo)

Entry hackathon Loops House. Karena tanpa paspor, **Track 3 (Self Agent ID) tidak
diikuti**. Yang dikerjakan:

| Track | Fokus | Status |
|---|---|---|
| 1 — Stablecoin Corridors | Textile FX, USD₮ → IDRX, bayar penerima eksternal | ✅ Python |
| 2 — Agent Vault + x402 | Login ke website biasa + bayar per-request | ✅ Python + sidecar Node |
| 4 — Altana Agent Wallets | Session key: spend cap, allowlist, expiry, revoke | ✅ Python + sidecar Bun |

## Timeline
- 20 Nov: enroll + attribution tag + ERC-8004
- 24 Nov & 4 Des: AskBots review
- 7 Des 09:00 GMT: submission close · 11 Des: winners

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env            # isi sesuai kredensial kamu
cd sidecars && npm install && cd ..   # untuk x402 + Altana
pytest -q
```

## Perintah

```bash
python -m src.cli onboarding            # checklist: apa yang masih harus kamu lakukan
python -m src.cli check                 # validasi env + chain + kode
python -m src.cli register-agent        # [WAJIB] daftar ERC-8004 di Celo mainnet
python -m src.cli registry              # cek agentId wallet kamu
python -m src.cli quote                 # [T1] firm quote, tanpa broadcast
python -m src.cli pay --dry-run          # [T1] simulasi alur
python -m src.cli pay                    # [T1] eksekusi + verifikasi tag

python -m src.cli signin --dry-run       # [T2] lihat urutan MCP
python -m src.cli av-catalog             # [T2] cetak mock token Agent Vault
python -m src.cli signin                 # [T2] login via Agent Vault
python -m src.cli x402-seller --dry-run  # [T2] simulasi seller lokal
python -m src.cli x402-seller            # [T2] jalankan seller di :3402
python -m src.cli x402 http://localhost:3402/premium   # [T2] bayar (terminal 2)

python -m src.cli altana --dry-run       # [T4] simulasi session key
python -m src.cli altana                 # [T4] grant -> execute -> revoke

python -m src.cli verify 0x...           # cek tag sebuah tx
```

## Arsitektur

- **`src/` (Python)** — orkestrasi + attribution tag ERC-8021 murni Python.
  Semua transaksi Track 1 dan calldata Track 4 ditandai di sini sebelum dikirim.
- **`src/erc8004.py`** — registrasi identitas (wajib). File registrasi disimpan
  sebagai `data:` URI di calldata, jadi tidak perlu hosting; `register-agent`
  otomatis mengisi `registrations.agentId` lalu memanggil `setAgentURI`.
- **`sidecars/x402-buyer.mjs`** — buyer resmi `@x402/fetch` v2. Tidak
  hand-assemble payload 402. Default asset USDC Celo mainnet, spend control
  eksplisit (`$1` / `100000` atomic).
- **`sidecars/x402-seller.mjs`** — seller resmi `@x402/hono` v2. Endpoint
  `GET /premium` dihargai $0.01–$0.10 USDC, difasilitasi `api.x402.celo.org`.
  Diperlukan `X402_API_KEY` (buat di x402.celo.org dengan GitHub sign-in untuk
  credit mainnet). Ini memberi kita endpoint berbayar nyata untuk Track 2.
- **`sidecars/altana-agent-wallet.ts`** — SDK `@altananetwork/sdk` dengan chain
  `CELO`: `createWallet` → `grantSession` (spend cap, allowlist kontrak, expiry)
  → `execute` → `revokeSession`. Policy diverifikasi onchain.
- **`src/agent_vault.py`** — klien MCP Python menjalankan MCP server resmi Agent
  Vault (`@agentvault/mcp`) lewat stdio, lalu memanggil `get_token_catalog`,
  `open_page`, `fill_login`, `click`, `get_session_outcome`, `close_session`.

## Catatan penting

- **Attribution code harus yang diasign saat enroll.** Kode self-derived tidak
  dikredit. `check` membandingkannya dengan `codeFromRepo(GITHUB_REPO)`.
- Tag di **calldata transaksi**, bukan di contract, dan **tidak bisa ditambah
  belakangan**.
- **Jangan menambah suffix dua kali** — `append_tag()` me-merge otomatis. Kalau
  pakai API key Textile, jangan kirim `includeAttribution`.
- Celo **mainnet** saja (42220). Sandbox Textile (BSC/Base Sepolia) hanya latihan.
- `RECIPIENT_ADDRESS` harus di luar tim dan tidak kamu fund sebelumnya.
- x402 **belum** membawa tag; daftarkan **PayTo address** saat sign-up facilitator.
- Untuk Agent Vault, sign-in saja sudah memenuhi syarat track; checkout kartu
  opsional. Jangan pakai kartu asli di `/demo-checkout`.

## Kredensial yang dibutuhkan (diisi di `.env`, jangan di-commit)

- `TAKER_PRIVATE_KEY`, `PAYOUT_ADDRESS`, `ATTRIBUTION_CODE`, `RECIPIENT_ADDRESS`
- Track 2: `AGENTVAULT_API_KEY` + token login dari dashboard Agent Vault;
  `BUYER_PRIVATE_KEY` (berisi USDC Celo) untuk x402
- Track 4: `ALTANA_ADMIN_PRIVATE_KEY` (admin wallet milik orang, bukan agent)

Belum ada transaksi nyata yang dijalankan — semua siap dieksekusi setelah `.env`
diisi dan kode enrollment diketahui.
