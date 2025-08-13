> [!NOTE]
> While a preview is already [available](https://visualfol.io/) for demonstration purposes, Visualfolio is in an early stage of development and is not ready for real-world use.

<br><br>

<p align="center">
  <a href="https://visualfol.io/" target="_blank" rel="noopener noreferrer">
    <img src="https://github.com/user-attachments/assets/91436dfa-7c73-4be2-8fba-8de1b9b4e864" alt="Visualfolio logo" style="width: 200px; height: auto;">
  </a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-3776AB" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Django-092E20" alt="Django">
  <img src="https://img.shields.io/badge/Visualization-Plotly-3F4F75" alt="Plotly">
  <img src="https://img.shields.io/badge/Styling-Tailwind%20CSS-06B6D4" alt="Tailwind CSS">
</p>

---

<p align="center">
  Visualfolio is a highly-visual <strong>personal finance dashboard</strong> that gives you a full view of all your holdings, transactions, and trades across bank accounts, investment platforms, and digital wallets.
</p>

<br>

<p align="center">
  <a href="https://visualfol.io/" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/Try%20Live%20Demo-visualfol.io-4F46E5?style=for-the-badge&logo=external-link&logoColor=white" alt="Try Live Demo">
  </a>
</p>
<br><br>

# Set up (production)
*(Linux Server)*

>The app is self-contained, the following commands automatically set a docker stack with **all required services** (Django + Postgres)

**1) Clone:**
```bash
git clone https://github.com/benvigano/visualfolio.git
cd visualfolio
```

**2) Copy .env template and fill in your environment varaibles:**
```bash
cp env.example .env
```
-- Replace the placeholders in `.env` with your variables


**3) Deploy:**
```bash
docker-compose up -d
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py migrate
```

**4) Set up external access:**

*Recommended: Cloudflare Tunnel*
```bash
# Authenticate with Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create visualfolio

# Get tunnel ID
cloudflared tunnel list

# Create config file (~/.cloudflared/config.yml)
# Add:
# tunnel: <tunnel-id>
# credentials-file: ~/.cloudflared/<tunnel-id>.json
# ingress:
#   - hostname: your-domain.com
#     service: http://localhost:8000
#   - service: http_status:404

# Add CNAME record: your-domain.com -> <tunnel-id>.cfargotunnel.com

# Run tunnel
cloudflared tunnel run visualfolio
```

*Standard: Reverse Proxy + SSL*
- Configure nginx/Apache with SSL certificates
- Point proxy to http://localhost:8000
- Uncomment ports in `docker-compose.yml` if needed

<br><br>

# Run locally (development)
*(Windows/macOS/Linux)*

>The app is self-contained, the following commands automatically set up a docker stack with **all required services** (Django + Postgres)

**1) Install Node.js  (on host, not in the container):**
- [Node.js](https://nodejs.org/).

**2) Install project dependencies:**
- In Django root directory (`visualfolio/visualfolio`) run:
  ```bash
  npm install
  ```

**3) Start the development servers:**
- **In one terminal**, start the Docker containers:
  ```bash
  docker-compose -f docker-compose.dev.yml --env-file env.dev.example up -d
  docker-compose -f docker-compose.dev.yml exec app-dev python manage.py makemigrations
  docker-compose -f docker-compose.dev.yml exec app-dev python manage.py migrate
  ```
- **In a second terminal**, start the Tailwind CSS watcher (on host machine):
  ```bash
  npm run watch:css
  ```

**4) Access at:** http://localhost:8001

<br><br>


# The app

### Streamgraph
The Home page Streamgraph is a specialized wealth visualization designed to visually separate **earnings/expenses** and **changes in asset value.**

<p align="center">
    <img src="https://github.com/user-attachments/assets/9418f0e2-85d4-4601-a480-def221e0c183" alt="Home page screen capture" style="width: 900px; height: auto;">
</p>

- The top boundary reflects transactions (earnings/expenses). An outgoing transaction is represented as a downward movement. An incoming transaction, instead, is represented by an upward extension of the stream. Transactions are represented as vertical movements as they happen instantaneously.
- The bottom boundary reflects investment profit or loss. The expansion here is inverted: an increase in asset value causes the stream to extend downwards, whereas a decrease in asset value makes the lower boundary move upwards, thus shrinking the stream.
- As a result, the thickness of the stream reflects the total asset value at all times.
<br><br>
**Notice:** Stack division is available only if the user does not use non-fiat currency assets for transactions (trades instead are supported by the visualization). If the user has performed transactions using assets of other classes, the streamgraph is displayed as a single area.

### Assets
Visualfolio aims to provide a unified view of all the user's assets across all their accounts by seamlessly aggregating data from multiple sources.
<p align="center">
    <img src="https://github.com/user-attachments/assets/b7c0ed5c-57fd-42c2-9ffa-899349c383e3" alt="Assets page screen capture" style="width: 900px; height: auto;">
</p>

### Sources of earning
<p align="center">
    <img src="https://github.com/user-attachments/assets/4050fc33-b15a-4f51-afe0-5ee923a073b4" alt="Earnings page screen capture" style="width: 900px; height: auto;">
</p>

<br><br>

# Roadmap
- Bank data API integration ([GoCardless](https://gocardless.com/bank-account-data/), [Salt Edge](https://www.saltedge.com/))
- Manual account setup for accounts not supported by the bank data API (single or batch-upload for transactions)
- Create logomark (add to logotype and as favicon)
