import csv
import os
import concurrent.futures
from nexus_harvester.utils.intel import get_smtp_intel, guess_domain

class NexusHarvester:
    def __init__(self, threads=50):
        self.threads = threads
        self.results = []
        # Billion-Dollar Standard Colors
        self.GOLD = "\033[93m"
        self.CYAN = "\033[96m"
        self.RED = "\033[91m"
        self.RESET = "\033[0m"

    def process_single_lead(self, lead):
        """Analyze a single lead record."""
        name = lead.get('Name') or lead.get('BusinessName')
        domain = lead.get('Domain')
        
        if not domain or domain == "N/A":
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
            lead.update({
                "Domain": "N/A", "Provider": "N/A", "SPF": "N/A", 
                "DMARC": "N/A", "Vulnerable": "N/A"
            })
        return lead

    def harvest_batch(self, input_csv, output_csv):
        """Process a CSV batch with high concurrency."""
        print(f"{self.GOLD}[*] Nexus Harvester: Starting batch enrichment...{self.RESET}")
        
        if not os.path.exists(input_csv):
            print(f"{self.RED}[!] Error: Input file {input_csv} not found.{self.RESET}")
            return

        with open(input_csv, 'r') as f:
            leads = list(csv.DictReader(f))

        print(f"{self.CYAN}[*] Spinning up {self.threads} threads for institutional audit...{self.RESET}")
        
        enriched_leads = []
        vuln_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_lead = {executor.submit(self.process_single_lead, lead): lead for lead in leads}
            count = 0
            for future in concurrent.futures.as_completed(future_to_lead):
                result = future.result()
                enriched_leads.append(result)
                if result.get("Vulnerable") == "YES":
                    vuln_count += 1
                count += 1
                if count % 500 == 0:
                    print(f"[*] Progress: {count}/{len(leads)}...")

        # Save to CSV
        if enriched_leads:
            fieldnames = enriched_leads[0].keys()
            os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
            with open(output_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(enriched_leads)
            
            print(f"{self.GOLD}[!] Batch complete. Result stored in: {output_csv}{self.RESET}")
            print(f"{self.RED}[!] Identified {vuln_count} vulnerable targets.{self.RESET}")
        
        return enriched_leads
