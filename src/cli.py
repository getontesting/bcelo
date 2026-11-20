"""CLI: check / quote / pay / verify / signin / x402 / altana."""
from __future__ import annotations

import argparse
import os

from web3 import HTTPProvider, Web3

from . import erc8004
from .agent import check_settings, pay_supplier
from .agent_vault import list_tokens, sign_in
from .altana import run as run_altana, transfer_calldata
from .attribution import code_from_repo, verify_tx
from .config import Settings, TOKENS
from .x402 import pay as pay_x402
from .x402_seller import serve as serve_x402


def _onboarding() -> None:
    """Checklist gabungan: mana yang sudah ada, mana yang masih harus dilakukan."""
    def filled(name: str) -> bool:
        value = os.getenv(name, "").strip().lower()
        if not value:
            return False
        placeholders = (
            "your_", "xxx", "contoh", "example", "external_recipient",
            "admin_wallet", "buyer_wallet", "owner/", "placeholder",
        )
        return not any(p in value for p in placeholders)

    def status(name: str, ok: bool, action: str) -> None:
        mark = "[OK]  " if ok else "[TODO]"
        print(f"{mark} {name}")
        if not ok:
            print(f"       -> {action}")

    code = os.getenv("ATTRIBUTION_CODE", "")
    repo = os.getenv("GITHUB_REPO", "")

    print("=== WAJIB (semua track) ===")
    print("[MANUAL] Enroll di loops.house/agents-open-for-business/enroll")
    print("       -> ambil kode attribution yang DIASIGN (bukan yang self-derived)")
    status(
        "ATTRIBUTION_CODE terisi & bukan placeholder",
        bool(code) and code != "celo_test1234",
        "isi kode dari hasil enroll ke .env",
    )
    status(
        "GITHUB_REPO terisi (repo publik)",
        bool(repo) and "owner/" not in repo,
        "push kode ke GitHub lalu isi GITHUB_REPO=owner/repo",
    )
    status(
        "ERC-8004 terdaftar",
        bool(os.getenv("AGENT_ID", "")),
        "jalankan: python -m src.cli register-agent",
    )
    status(
        "Saldo CELO untuk gas + USDT untuk Textile",
        False,
        "bridge/beli keduanya ke wallet agent di Celo mainnet",
    )
    status(
        "Penerima eksternal",
        filled("RECIPIENT_ADDRESS"),
        "isi RECIPIENT_ADDRESS (di luar tim, jangan kamu fund)",
    )

    print("\n=== TRACK 1 ===")
    status(
        "Textile API key (opsional)",
        bool(os.getenv("TEXTILE_API_KEY", "")),
        "kosongkan pun bisa: takerProof EIP-712 otomatis",
    )

    print("\n=== TRACK 2 ===")
    status(
        "Agent Vault API key + token login",
        filled("AGENTVAULT_API_KEY") and filled("AGENTVAULT_USERNAME_TOKEN"),
        "dashboard Agent Vault: buat key, simpan login, isi token di .env",
    )
    status(
        "BUYER_PRIVATE_KEY valid",
        filled("BUYER_PRIVATE_KEY"),
        "isi buyer wallet (boleh sama dengan agent) yang punya USDC",
    )
    status(
        "Endpoint x402 untuk dibayar",
        filled("X402_ENDPOINT"),
        "isi X402_ENDPOINT dengan URL endpoint berbayar yang nyata",
    )

    print("\n=== TRACK 4 ===")
    status(
        "ALTANA_ADMIN_PRIVATE_KEY",
        filled("ALTANA_ADMIN_PRIVATE_KEY"),
        "isi admin wallet (milik orang, bukan session key agent)",
    )

    print("\n=== MANUAL TERAKHIR ===")
    print("[MANUAL] Pastikan repo GitHub PUBLIC dan masih bisa diakses saat judging")
    print("[MANUAL] Submit di Loops House sebelum 7 Des 09:00 GMT")
    print("[MANUAL] Sebutkan NAMA USER + pekerjaan nyata yang selesai di submission")


def main() -> None:
    parser = argparse.ArgumentParser(prog="bcelo")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="validasi env + identitas agent")
    sub.add_parser("quote", help="[Track 1] firm quote Textile FX, tanpa broadcast")
    pay = sub.add_parser("pay", help="[Track 1] alur lengkap + verifikasi tag")
    pay.add_argument("--dry-run", action="store_true")
    verify = sub.add_parser("verify", help="cek attribution tag sebuah tx")
    verify.add_argument("tx_hash")

    signin = sub.add_parser("signin", help="[Track 2] login via Agent Vault MCP")
    signin.add_argument("--dry-run", action="store_true")
    sub.add_parser(
        "av-catalog", help="[Track 2] cetak mock token Agent Vault dari catalog"
    )
    x402 = sub.add_parser("x402", help="[Track 2] bayar endpoint x402")
    x402.add_argument("url", nargs="?", default="")
    x402.add_argument("--dry-run", action="store_true")
    seller = sub.add_parser("x402-seller", help="[Track 2] jalankan seller x402 lokal")
    seller.add_argument("--port", type=int, default=3402)
    seller.add_argument("--dry-run", action="store_true")
    altana = sub.add_parser("altana", help="[Track 4] session key Altana di Celo")
    altana.add_argument("--dry-run", action="store_true")
    sub.add_parser("onboarding", help="checklist apa yang masih harus kamu lakukan")
    sub.add_parser("registry", help="cek agent ID ERC-8004 untuk wallet agent")

    register = sub.add_parser(
        "register-agent", help="daftarkan identitas ERC-8004 di Celo mainnet"
    )
    register.add_argument("--name", default="Loops Business Agent")
    register.add_argument(
        "--description",
        default="Agent that pays local stablecoin suppliers via Textile FX on Celo",
    )
    register.add_argument(
        "--endpoint", default="https://github.com/owner/repo"
    )

    args = parser.parse_args()

    if args.command == "check":
        settings = Settings.from_env()
        w3 = Web3(HTTPProvider(settings.rpc_url))
        account = w3.eth.account.from_key(settings.private_key)
        taker = Web3.to_checksum_address(account.address)
        warnings = check_settings(settings, taker)
        print(f"agent address : {taker}")
        print(f"chain         : {w3.eth.chain_id}")
        print(f"attribution   : {settings.attribution_code}")
        if settings.github_repo:
            print(f"code dari repo: {code_from_repo(settings.github_repo)}")
        print(f"payout        : {settings.payout_address}")
        for item in warnings:
            print(f"[WARN] {item}")
        if not warnings:
            print("[OK] konfigurasi siap")
        return

    if args.command == "quote":
        pay_supplier(Settings.from_env(), dry_run=True)
        return

    if args.command == "pay":
        result = pay_supplier(Settings.from_env(), dry_run=args.dry_run)
        if result:
            print("\n=== RINGKASAN TRACK 1 ===")
            print(f"swap     : {result.swap_hash}")
            print(f"payout   : {result.payout_hash}")
            print(f"semua tag valid: {all(r['ok'] for r in result.verified)}")
        return

    if args.command == "verify":
        settings = Settings.from_env()
        w3 = Web3(HTTPProvider(settings.rpc_url))
        print(verify_tx(w3, args.tx_hash, [settings.attribution_code]))
        return

    if args.command == "av-catalog":
        print(list_tokens())
        return

    if args.command == "signin":
        sign_in(
            url=os.getenv("AGENTVAULT_SIGNIN_URL", ""),
            username_selector=os.getenv(
                "AGENTVAULT_USERNAME_SELECTOR", "input[type='email']"
            ),
            username_token=os.getenv("AGENTVAULT_USERNAME_TOKEN", ""),
            password_selector=os.getenv(
                "AGENTVAULT_PASSWORD_SELECTOR", "input[type='password']"
            ),
            password_token=os.getenv("AGENTVAULT_PASSWORD_TOKEN", ""),
            submit_selector=os.getenv(
                "AGENTVAULT_SUBMIT_SELECTOR", "button[type='submit']"
            ),
            success_selector=os.getenv("AGENTVAULT_SUCCESS_SELECTOR", "#dashboard"),
            dry_run=args.dry_run,
        )
        return

    if args.command == "x402-seller":
        serve_x402(port=args.port, dry_run=args.dry_run)
        return

    if args.command == "x402":
        url = args.url or os.getenv("X402_ENDPOINT", "")
        result = pay_x402(url, dry_run=args.dry_run)
        if result:
            print(f"status: {result.status}")
            if result.payment:
                print(f"payment: {result.payment}")
        return

    if args.command == "altana":
        code = os.getenv("ATTRIBUTION_CODE", "celo_test1234")
        recipient = os.getenv("RECIPIENT_ADDRESS", "")
        if args.dry_run and not recipient:
            recipient = "0x1111111111111111111111111111111111111111"
        amount = int(os.getenv("ALTANA_TRANSFER_AMOUNT", "1000000"))
        result = run_altana(
            to=TOKENS["USDT"],
            calldata=transfer_calldata(TOKENS["USDT"], recipient, amount),
            recipient=recipient,
            amount=amount,
            attribution_code=code,
            dry_run=args.dry_run,
        )
        if result:
            print("\n=== RINGKASAN TRACK 4 ===")
            print(f"wallet   : {result.wallet}")
            print(f"status   : {result.status}")
            print(f"tx       : {result.tx_hash}")
            print(f"revoked  : {result.revoked}")
        return

    if args.command == "onboarding":
        _onboarding()
        return

    if args.command == "registry":
        settings = Settings.from_env()
        w3 = Web3(HTTPProvider(settings.rpc_url))
        account = w3.eth.account.from_key(settings.private_key)
        raw_id = os.getenv("AGENT_ID", "").strip()
        if raw_id.isdigit():
            agent_id = int(raw_id)
            owner = erc8004.agent_owner(w3, agent_id)
            print(f"agentId: {agent_id}")
            print(f"owner  : {owner}")
            print(f"cocok dengan wallet agent: {owner.lower() == account.address.lower()}")
        else:
            agent_id = erc8004.agent_id_for_owner(w3, account.address)
            print(f"owner  : {account.address}")
            print(f"agentId: {agent_id if agent_id is not None else 'BELUM ADA'}")
        return

    if args.command == "register-agent":
        settings = Settings.from_env()
        w3 = Web3(HTTPProvider(settings.rpc_url))
        account = w3.eth.account.from_key(settings.private_key)
        existing = erc8004.agent_id_for_owner(w3, account.address)
        if existing is not None:
            print(f"Wallet ini sudah punya agentId {existing}. Skip.")
            return

        doc = erc8004.build_registration(
            name=args.name,
            description=args.description,
            endpoint=args.endpoint,
            x402_support=True,
        )
        uri = erc8004.to_data_uri(doc)
        agent_id = erc8004.register(
            w3, settings.private_key, uri, settings.attribution_code
        )
        print(f"Terdaftar sebagai agentId {agent_id}")

        # Tambahkan registrations ke file, lalu update agentURI.
        doc = erc8004.build_registration(
            name=args.name,
            description=args.description,
            endpoint=args.endpoint,
            x402_support=True,
            agent_id=agent_id,
        )
        tx = erc8004.set_agent_uri(
            w3, settings.private_key, agent_id, erc8004.to_data_uri(doc),
            settings.attribution_code,
        )
        print(f"agentURI diupdate: {tx}")
        print(f"Simpan ke .env: AGENT_ID={agent_id}")
        return


if __name__ == "__main__":
    main()
