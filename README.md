# Nexus Harvester V2.0 🦁🛰️

Autonomous lead extraction and technical vulnerability analysis engine. Built to **Billion-Dollar Institutional Standards** for the Nexus OS pride.

## 🚀 Overview

Nexus Harvester is a high-performance OSINT and technical auditing tool designed to identify and expand target identities within vulnerable infrastructures. It specializes in DNS/SMTP reconnaissance and mass identity generation for institutional outreach.

## 🛠️ Components

- **NexusHarvester Engine**: Multi-threaded technical auditor (MX/SPF/DMARC/Domain discovery).
- **Identity Generator**: High-fidelity professional identity synthesizer.
- **CLI Interface**: Institutional-grade command line control.

## 📦 Installation

```bash
git clone git@github.com:maturelion/nexus-lead-harvester.git
cd nexus-lead-harvester
pip install -e .
```

## 🎯 Usage

### 1. Technical Audit (Recon)
Process a raw list of business names to discover domains and technical vulnerabilities.

```bash
nexus-hunt audit --input leads.csv --output audited_leads.csv --threads 100
```

### 2. Mass Identity Harvest
Generate institutional identities for the audited targets.

```bash
nexus-hunt harvest --input audited_leads.csv --output payload_50k.csv --count 50000
```

## 💎 Features

- **High Concurrency**: Optimized for 50-100+ concurrent threads.
- **Institutional Standards**: Colors and reporting styled for elite operations.
- **Vulnerability Heatmapping**: Automatic detection of spoofable domains (SPF/DMARC debt).
- **Google Workspace Optimization**: Specialized handling for GSuite infrastructures.

---
*Maintained by the Sky Lion Pride.*
