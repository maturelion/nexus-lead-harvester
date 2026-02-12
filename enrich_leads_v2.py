import csv
import dns.resolver
import concurrent.futures
import os
from datetime import datetime

# Institutional Standards
GOLD = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

INPUT_FILE = "/root/ai-workforce-os/output/marketing/master_leads_5000.csv"
OUTPUT_FILE = "/root/ai-workforce-os/output/marketing/enriched_leads_5000.csv"

def get_smtp_intel(domain):
    intel = {"provider": "Unknown", "spf": "None", "dmarc": "None", "vulnerable": False}
    try:
        # Provider via MX
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).lower()
            if "google" in mx_host: intel["provider"] = "Google Workspace"
            elif "outlook" in mx_host: intel["provider"] = "Microsoft 365"
            else: intel["provider"] = mx_host.rstrip('.')
        except: pass

        # SPF
        try:
            spf_records = dns.resolver.resolve(domain, 'TXT')
            for record in spf_records:
                if "v=spf1" in str(record):
                    intel["spf"] = "Found"
                    break
        except: pass

        # DMARC
        try:
            dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
            for record in dmarc_records:
                if "v=DMARC1" in str(record):
                    intel["dmarc"] = str(record).replace('"', '')
                    break
        except: pass

        # Vulnerability Check
        if intel["spf"] == "None" or "p=none" in intel["dmarc"].lower() or intel["dmarc"] == "None":
            intel["vulnerable"] = True

    except: pass
    return intel

def guess_domain(name):
    clean_name = "".join(filter(str.isalnum, name.lower()))
    for ext in ['com', 'org', 'net', 'io']:
        domain = f"{clean_name}.{ext}"
        try:
            dns.resolver.resolve(domain, 'A')
            return domain
        except: continue
    return None

def process_lead(lead):
    name = lead['Name']
    domain = guess_domain(name)
    if domain:
        intel = get_smtp_intel(domain)
        lead.update({
            "Domain": domain,
            "Provider": intel["provider"],
            "SPF": intel["spf"],
            "DMARC": intel["dmarc"],
            "Vulnerable": "YES" if intel["vulnerable"] else "NO"
        })
    else:
        lead.update({"Domain": "N/A", "Provider": "N/A", "SPF": "N/A", "DMARC": "N/A", "Vulnerable": "N/A"})
    return lead

def main():
    print(f"{GOLD}[*] Starting Mass Enrichment of 5,000 leads...{RESET}")
    
    with open(INPUT_FILE, 'r') as f:
        leads = list(csv.DictReader(f))
    
    # Pre-calculate fieldnames
    sample_lead = process_lead(leads[0].copy())
    fieldnames = sample_lead.keys()
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    vuln_count = 0
    # Open file for real-time writing
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        print(f"{CYAN}[*] Spinning up 50 threads for high-speed OSINT audit...{RESET}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_lead = {executor.submit(process_lead, lead): lead for lead in leads}
            count = 0
            for future in concurrent.futures.as_completed(future_to_lead):
                result = future.result()
                writer.writerow(result)
                f.flush() # Ensure it writes to disk immediately
                if result.get("Vulnerable") == "YES":
                    vuln_count += 1
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count}/5000...")

    print(f"\n{GOLD}[!] Enrichment complete. Result stored in: {OUTPUT_FILE}{RESET}")
    print(f"{RED}[!] Found {vuln_count} VULNERABLE targets ready for campaign entry.{RESET}")

if __name__ == "__main__":
    main()
