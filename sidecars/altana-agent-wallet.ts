// Altana session key di Celo mainnet: fund -> grant -> execute -> revoke.
// Policy (spend cap, allowlist kontrak, expiry) ditegakkan onchain.
// Wallet Altana harus punya saldo supaya relay bisa menagih fee.
import {
  createClient,
  CELO,
  signerFromPrivateKey,
  createPrivateKeySigner,
  NATIVE_TOKEN,
} from "@altananetwork/sdk";
import {
  getAddress,
  erc20Abi,
  createPublicClient,
  http,
  parseUnits,
  type Hex,
} from "viem";
import { celo } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";

function env(name: string, fallback = ""): string {
  return (process.env[name] || fallback).trim();
}
function key(name: string): Hex {
  let raw = env(name);
  if (raw && !raw.startsWith("0x")) raw = "0x" + raw;
  return raw as Hex;
}

const adminKey = key("ALTANA_ADMIN_PRIVATE_KEY");
const callTo = env("ALTANA_CALL_TO");
const callData = env("ALTANA_CALL_DATA") as Hex;
if (!adminKey) throw new Error("ALTANA_ADMIN_PRIVATE_KEY belum diisi");
if (!callTo || !callData) {
  throw new Error("ALTANA_CALL_TO dan ALTANA_CALL_DATA wajib diisi");
}

const usdt = getAddress("0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e");
const allowed = env("ALTANA_ALLOWED_CONTRACTS", callTo)
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean)
  .map((s) => ({ to: getAddress(s) }));

const client = createClient({ chains: [CELO] });
const admin = signerFromPrivateKey(adminKey);

// Wallet non-custodial milik orang (admin key tidak pernah diberikan ke agent).
const wallet = await client.createWallet({ signer: admin });

// --- Fund wallet Altana dengan USDT dari admin EOA ---
const publicClient = createPublicClient({
  chain: celo,
  transport: http(env("CELO_RPC_URL", "https://forno.celo.org")),
});
const adminAccount = privateKeyToAccount(adminKey);
const fundAmount = BigInt(env("ALTANA_FUND_AMOUNT", "2000000")); // 2 USDT
let fundHash: Hex | null = null;
const balance = await publicClient.readContract({
  address: usdt,
  abi: erc20Abi,
  functionName: "balanceOf",
  args: [wallet.address],
});
if (balance < fundAmount) {
  fundHash = await publicClient.writeContract({
    account: adminAccount,
    address: usdt,
    abi: erc20Abi,
    functionName: "transfer",
    args: [wallet.address, fundAmount],
    chain: celo,
  });
  await publicClient.waitForTransactionReceipt({ hash: fundHash });
}

// Fee relay Altana dibayar dari wallet Altana dalam native CELO.
const nativeBalance = await publicClient.getBalance({ address: wallet.address });
const nativeNeed = parseUnits(env("ALTANA_FUND_CELO", "0.2"), 18);
if (nativeBalance < nativeNeed) {
  const h = await publicClient.sendTransaction({
    account: adminAccount,
    to: wallet.address,
    value: nativeNeed,
    chain: celo,
  });
  await publicClient.waitForTransactionReceipt({ hash: h });
}

// Wallet counterfactual harus diaktifkan dulu lewat execute pertama.
// Ini yang register admin key onchain — tanpa ini grantSession ditolak relay.
const activation = await client.execute({
  wallet,
  signer: admin,
  calls: { to: wallet.address, value: 0n },
  feeToken: NATIVE_TOKEN,
  // Kita sudah punya ERC-8004 agentId 10077 — jangan bayar registrasi kedua.
  agentIdentity: false,
});

const session = await client.grantSession({
  wallet,
  signer: admin,
  sessionSigner: createPrivateKeySigner(),
  permissions: {
    calls: allowed,
    spend: [
      {
        limit: BigInt(env("ALTANA_SPEND_LIMIT", "1000000")), // 1 USDT/hari
        period: "day",
      },
    ],
  },
  expiry:
    Math.floor(Date.now() / 1000) +
    Number(env("ALTANA_EXPIRY_SECONDS", "86400")),
  feeToken: NATIVE_TOKEN,
});

const result = await client.execute({
  session,
  calls: [{ to: getAddress(callTo), data: callData, value: 0n }],
  feeToken: NATIVE_TOKEN,
});

let revoked = false;
if (env("ALTANA_REVOKE", "1") === "1") {
  await client.revokeSession({
    wallet,
    signer: admin,
    session,
    feeToken: NATIVE_TOKEN,
  });
  revoked = true;
}

console.log(
  JSON.stringify({
    wallet: wallet.address,
    fundHash,
    activationHash: activation.transactionHash,
    status: result.status,
    txHash: result.transactionHash,
    revoked,
  })
);
