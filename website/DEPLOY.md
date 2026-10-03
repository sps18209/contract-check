# TopContractReview on Cloudflare

Source: sps18209/contract-check. Worker name: topcontractreview.

In Cloudflare Workers & Pages, create a Worker connected to this GitHub repository, production branch main, root directory /. Set build command to npm run build and deploy command to npx wrangler deploy. Keep PYTHON_VERSION at 3.12 or later and NODE_VERSION at 22 or later. Install dependencies with npm install (there is no lock file yet).

The root wrangler.jsonc uses Workers Static Assets with ./website/public and custom domains topcontractreview.com and www.topcontractreview.com. Both domains must be in the selected Cloudflare account. The generated site contains the complete skill ZIPs, .skill archive, references, and forms; no contract text is submitted to the website.

Local review: npm install, npm run dev. Build: npm run build. CLI deployment: npm run deploy after Cloudflare login. No Cloudflare credentials are included in the source. Deployment and DNS verification remain required before claiming the domain is live.
