import dns.resolver
import asyncio
from .validator import EmailValidator

def get_smtp_intel(domain):
    """Analyze DNS for SMTP provider and spoofability using elite validator."""
    validator = EmailValidator()
    
    # We use sync wrapper for async validator logic where possible or keep it simple
    # but since this is a utility, let's just use the elite provider identification logic
    
    intel = {
        "provider": "Unknown",
        "spf": "None",
        "dmarc": "None",
        "vulnerable": False,
        "details": ""
    }
    
    try:
        # Get MX to identify provider
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(record.exchange).lower() for record in mx_records]
            intel["provider"] = validator.get_provider(mx_hosts)
            if intel["provider"] == "Microsoft": intel["provider"] = "Microsoft 365"
            elif intel["provider"] == "Google": intel["provider"] = "Google Workspace"
        except:
            intel["details"] += "MX Records Missing; "

        # Heuristic check for spoofability (Sync version of elite logic)
        try:
            spf_exists = False
            dmarc_exists = False
            weak_spf = False
            weak_dmarc = False
            
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                txt_content = str(record).lower()
                if "v=spf1" in txt_content:
                    spf_exists = True
                    intel["spf"] = "Found"
                    if "+all" in txt_content or "?all" in txt_content or ("~all" not in txt_content and "-all" not in txt_content):
                        weak_spf = True
            
            try:
                dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
                for record in dmarc_records:
                    txt_content = str(record).lower()
                    if "v=dmarc1" in txt_content:
                        dmarc_exists = True
                        intel["dmarc"] = txt_content.replace('"', '')
                        if "p=none" in txt_content:
                            weak_dmarc = True
            except: pass

            if not spf_exists or not dmarc_exists or weak_spf or weak_dmarc:
                intel["vulnerable"] = True
        except: pass

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
