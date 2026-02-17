import csv
import random
import os

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
POSITIONS = ["CEO", "CTO", "CISO", "Director", "Manager", "Lead", "Admin"]

def generate_identities(domains, target_count=50000):
    """Generate professional identities for target domains."""
    identities = []
    seen_emails = set()
    
    per_domain = (target_count // len(domains)) + 1
    
    for domain_info in domains:
        domain = domain_info['Domain']
        org_name = domain_info.get('Name', 'Organization')
        
        for _ in range(per_domain):
            if len(identities) >= target_count: break
            
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            
            patterns = [
                f"{fn.lower()}.{ln.lower()}@{domain}",
                f"{fn[0].lower()}{ln.lower()}@{domain}",
                f"{fn.lower()}@{domain}"
            ]
            email = random.choice(patterns)
            
            if email not in seen_emails:
                pos = random.choice(POSITIONS)
                identities.append({
                    "Name": f"{fn} {ln}",
                    "Email": email,
                    "Position": pos,
                    "Organization": org_name
                })
                seen_emails.add(email)
                
    # Fill remaining
    while len(identities) < target_count:
        domain_info = random.choice(domains)
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = f"{fn.lower()}{ln.lower()}{random.randint(1,99)}@{domain_info['Domain']}"
        if email not in seen_emails:
            identities.append({
                "Name": f"{fn} {ln}",
                "Email": email,
                "Position": random.choice(POSITIONS),
                "Organization": domain_info.get('Name', 'Organization')
            })
            seen_emails.add(email)
            
    return identities
