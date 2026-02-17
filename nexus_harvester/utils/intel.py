import dns.resolver

def get_smtp_intel(domain):
    """Analyze DNS for SMTP provider and spoofability."""
    intel = {
        "provider": "Unknown",
        "spf": "None",
        "dmarc": "None",
        "vulnerable": False,
        "details": ""
    }
    
    try:
        # Provider via MX
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).lower()
            if "google" in mx_host or "aspmx" in mx_host:
                intel["provider"] = "Google Workspace"
            elif "outlook" in mx_host or "protection.outlook" in mx_host:
                intel["provider"] = "Microsoft 365"
            elif "zoho" in mx_host:
                intel["provider"] = "Zoho Mail"
            else:
                intel["provider"] = mx_host.rstrip('.')
        except:
            intel["details"] += "MX Records Missing; "

        # SPF Check
        try:
            spf_records = dns.resolver.resolve(domain, 'TXT')
            for record in spf_records:
                if "v=spf1" in str(record):
                    intel["spf"] = "Found"
                    break
        except:
            intel["spf"] = "None"

        # DMARC Check
        try:
            dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
            for record in dmarc_records:
                if "v=DMARC1" in str(record):
                    intel["dmarc"] = str(record).replace('"', '')
                    break
        except:
            intel["dmarc"] = "None"

        # Vulnerability Heuristics
        if intel["spf"] == "None" or intel["dmarc"] == "None" or "p=none" in intel["dmarc"].lower():
            intel["vulnerable"] = True
            
    except Exception as e:
        intel["details"] += f"Error: {str(e)}"
        
    return intel

def guess_domain(name):
    """Heuristic domain discovery from business name."""
    clean_name = "".join(filter(str.isalnum, name.lower()))
    for ext in ['com', 'org', 'net', 'io', 'edu']:
        domain = f"{clean_name}.{ext}"
        try:
            dns.resolver.resolve(domain, 'A')
            return domain
        except:
            continue
    return None
