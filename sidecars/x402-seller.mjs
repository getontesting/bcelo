// Seller x402 di Celo mainnet — menyediakan endpoint berbayar untuk Track 2.
// Jalankan: node x402-seller.mjs   (lihat src/cli.py x402-seller)
import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { paymentMiddleware, x402ResourceServer } from "@x402/hono";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { getAddress } from "viem";

const NETWORK = "eip155:42220";
// USDT didukung facilitator Celo (eip3009). Kita punya saldo USDT, USDC nol.
const ASSET = getAddress("0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e");
const ASSET_EXTRA = { name: "Tether USD", version: "1" };

const key = process.env.X402_API_KEY;
const payToRaw = process.env.SELLER_PAY_TO || process.env.PAYOUT_ADDRESS;
if (!key) throw new Error("X402_API_KEY belum diisi (buat di x402.celo.org)");
if (!payToRaw) throw new Error("SELLER_PAY_TO / PAYOUT_ADDRESS belum diisi");

const payTo = getAddress(payToRaw);
const port = Number(process.env.X402_SELLER_PORT || 3402);

const facilitator = new HTTPFacilitatorClient({
  url: "https://api.x402.celo.org",
  createAuthHeaders: async () => {
    const h = { "X-API-Key": key };
    return { verify: h, settle: h, supported: h };
  },
});

const server = new x402ResourceServer(facilitator);
server.register("eip155:*", new ExactEvmScheme());

const routes = {
  "GET /premium": {
    accepts: [
      {
        scheme: "exact",
        network: NETWORK,
        payTo,
        price: {
          amount: process.env.X402_PRICE || "10000", // $0.10 default, 6 decimals
          asset: ASSET,
          extra: ASSET_EXTRA,
        },
      },
    ],
    description: "Paid data endpoint on Celo mainnet (Agents Open for Business)",
  },
};

const app = new Hono();
app.get("/health", (c) => c.json({ ok: true, network: NETWORK }));
app.use(paymentMiddleware(routes, server));
app.get("/premium", (c) =>
  c.json({
    data: "real job completed — paid per request over x402 on Celo",
    paidTo: payTo,
  })
);

console.log(`x402 seller listening on http://localhost:${port} (${NETWORK})`);
serve({ fetch: app.fetch, port });
