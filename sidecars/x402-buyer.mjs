// Buyer x402 — pakai paket resmi @x402/fetch v2.
// Dipanggil dari Python: node x402-buyer.mjs <url>
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { getAddress } from "viem";

const url = process.argv[2];
if (!url) {
  console.error("usage: node x402-buyer.mjs <https://endpoint-berbayar>");
  process.exit(2);
}

const key = process.env.BUYER_PRIVATE_KEY;
if (!key) throw new Error("BUYER_PRIVATE_KEY belum diisi");

const NETWORK = "eip155:42220"; // Celo mainnet
const USDC = getAddress("0xcebA9300f2b948710d2653dD7B07f33A8B32118C");

const account = privateKeyToAccount(key);
const client = new x402Client();

// Jangan pakai spendControls:false. Cantumkan asset secara eksplisit.
client.setSpendControls({
  allowedAssets: [
    {
      network: NETWORK,
      asset: USDC,
      maxAmountPerPayment: process.env.X402_MAX_AMOUNT || "100000", // $0.10
    },
  ],
  maxAmountPerPayment: process.env.X402_MAX_USD || "$1",
});

// { rpcUrl } penting: scheme butuh baca chain untuk Permit2.
client.register(
  "eip155:*",
  new ExactEvmScheme(account, {
    rpcUrl: process.env.CELO_RPC_URL || "https://forno.celo.org",
  })
);

const payFetch = wrapFetchWithPayment(fetch, client);
const res = await payFetch(url);
const body = await res.text();

let payment = null;
const header =
  res.headers.get("payment-response") || res.headers.get("x-payment-response");
if (header) {
  try {
    payment = JSON.parse(Buffer.from(header, "base64").toString("utf8"));
  } catch {
    payment = { raw: header };
  }
}

console.log(JSON.stringify({ status: res.status, body, payment }));
