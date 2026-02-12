# Nexus Lead Harvester V2.0 🦁🛰️

Autonomous lead extraction and technical vulnerability analysis engine. Part of the Nexus OS offensive stack.

## Components

- **`lead_generator_cli.py`**: Interactive hunt engine with SMTP/DNS intel.
- **`fetch_real_leads.mjs`**: OSINT extractor using Playwright.
- **`automated_hunt.py`**: Multi-threaded directory crawler.
- **`enrich_leads_v2.py`**: Technical audit engine (SPF/DMARC/SMTP).
- **`mass_harvest_5000.py`**: Scaling engine for high-volume identity generation.

## Standards

Built to **Billion-Dollar Institutional Standards**. 
- Stealth-first OSINT
- Real-time vulnerability filtering
- Multi-channel identity verification

## Usage

1. Install dependencies:
   ```bash
   pip install dnspython requests
   npm install playwright
   ```
2. Run the hunt:
   ```bash
   python lead_generator_cli.py --run
   ```

---
*Maintained by the Sky Lion Pride.*
