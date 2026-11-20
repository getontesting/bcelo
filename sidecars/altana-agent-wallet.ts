// Altana session key di Celo mainnet: grant -> execute -> revoke.
// Policy (spend cap, allowlist kontrak, expiry) ditegakkan onchain.
// Dipanggil dari Python: bun run altana-agent-wallet.ts
import {
  createClient,
  CELO,
  signerFromPrivateKey,
  createPrivateKeySigner,
} from "@altananetwork/sdk";
import { getAddress, type Hex } from "viem";

function env(name: string, fallback = ""): string {
  return (process.env[name] || fallback).trim();
}

let adminKeyRaw = env("ALTANA_ADMIN_PRIVATE_KEY");
if (adminKeyRaw && !adminKeyRaw.startsWith("0x")) adminKeyRaw = "0x" + adminKeyRaw;
const adminKey = adminKeyRaw as Hex;
const callTo = env("ALTANA_CALL_TO");
const callData = env("ALTANA_CALL_DATA") as Hex;
if (!adminKey) throw new Error("ALTANA_ADMIN_PRIVATE_KEY belum diisi");
if (!callTo || !callData) {
  throw new Error("ALTANA_CALL_TO dan ALTANA_CALL_DATA wajib diisi");
}

const allowed = env("ALTANA_ALLOWED_CONTRACTS", callTo)
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean)
  .map((s) => ({ to: getAddress(s) }));

const client = createClient({ chains: [CELO] });
const admin = signerFromPrivateKey(adminKey);

// Wallet non-custodial milik orang (admin key tidak pernah diberikan ke agent).
const wallet = await client.createWallet({ signer: admin });

const session = await client.grantSession({
  wallet,
  signer: admin,
  sessionSigner: createPrivateKeySigner(), // kunci agent, generated
  permissions: {
    calls: allowed,
    spend: [
      {
        limit: BigInt(env("ALTANA_SPEND_LIMIT", "1000000")), // 1 USDC (6 dp)
        period: "day",
      },
    ],
  },
  expiry:
    Math.floor(Date.now() / 1000) +
    Number(env("ALTANA_EXPIRY_SECONDS", "86400")),
});

const result = await client.execute({
  session,
  calls: [{ to: getAddress(callTo), data: callData, value: 0n }],
});

let revoked = false;
if (env("ALTANA_REVOKE", "1") === "1") {
  await client.revokeSession({ wallet, signer: admin, session });
  revoked = true;
}

console.log(
  JSON.stringify({
    wallet: wallet.address,
    status: result.status,
    txHash: result.transactionHash,
    revoked,
  })
);
