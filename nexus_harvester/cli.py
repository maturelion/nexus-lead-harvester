import argparse
import sys
import csv
import asyncio
from nexus_harvester.engine import NexusHarvester
from nexus_harvester.generator import generate_identities
from nexus_harvester.utils.validator import process_list
from nexus_harvester.directory import GSuiteDirectoryScraper

def main():
    parser = argparse.ArgumentParser(description="Nexus Harvester CLI - Billion Dollar Standards")
    subparsers = parser.add_subparsers(dest="command")

    # Audit Command
    audit_parser = subparsers.add_parser("audit", help="Audit a CSV of leads for technical vulnerabilities")
    audit_parser.add_argument("--input", required=True, help="Input CSV file")
    audit_parser.add_argument("--output", required=True, help="Output CSV file")
    audit_parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")

    # Directory Command (Internal Scrape)
    dir_parser = subparsers.add_parser("directory", help="Scrape internal GSuite directory using session token")
    dir_parser.add_argument("--session", required=True, help="Exfiltrated Bearer/Session Token")
    dir_parser.add_argument("--domain", required=True, help="Target domain")

    # Validate Command (Deep Handshake)
    validate_parser = subparsers.add_parser("validate", help="Perform elite SMTP handshake validation")
    validate_parser.add_argument("--input", required=True, help="Input file (txt/csv)")
    validate_parser.add_argument("--output", required=True, help="Output CSV path")
    validate_parser.add_argument("--concurrency", type=int, default=100, help="Concurrent handshake threads")
    validate_parser.add_argument("--sender", default="verify@example.com", help="Sender email for handshake")

    # Harvest Command
    harvest_parser = subparsers.add_parser("harvest", help="Generate mass identities from audited domains")
    harvest_parser.add_argument("--input", required=True, help="Audited CSV file (output from audit)")
    harvest_parser.add_argument("--output", required=True, help="Output CSV file for identities")
    harvest_parser.add_argument("--count", type=int, default=50000, help="Target number of identities")

    args = parser.parse_args()

    if args.command == "audit":
        harvester = NexusHarvester(threads=args.threads)
        harvester.harvest_batch(args.input, args.output)
    
    elif args.command == "validate":
        asyncio.run(process_list(args.input, args.output, args.concurrency, args.sender))

    elif args.command == "directory":
        scraper = GSuiteDirectoryScraper(args.session)
        asyncio.run(scraper.scrape_people_api())

    elif args.command == "harvest":
        print(f"[*] Loading domains from {args.input}...")
        domains = []
        with open(args.input, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Domain') and row.get('Domain') != "N/A":
                    # Only harvest from Google Workspace for high fidelity if requested, or all
                    domains.append(row)
        
        if not domains:
            print("[!] No domains found in input file.")
            return

        print(f"[*] Generating {args.count} identities across {len(domains)} domains...")
        identities = generate_identities(domains, target_count=args.count)
        
        with open(args.output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=identities[0].keys())
            writer.writeheader()
            writer.writerows(identities)
        
        print(f"[!] Successfully generated {len(identities)} identities stored in {args.output}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
