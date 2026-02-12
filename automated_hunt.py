import requests
import re
import csv
import os
import concurrent.futures

DOMAINS = [
    "academiamoderna.org",
    "aerostemacademy.org",
    "alltribescharter.org",
    "almafamilyservices.com",
    "americaresfoundation.com",
    "anaheimelementary.org",
    "arisehigh.com",
    "asacharter.com",
    "villagecharteracademy.com",
    "yubacitycharter.com"
]

ENDPOINTS = [
    "/apps/staff/",
    "/about/staff/",
    "/staff-directory/",
    "/our-team/",
    "/apps/pages/index.jsp?uREC_ID= staff",
    "/faculty-and-staff/",
    "/about/leadership/"
]

def hunt_staff(domain):
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for ep in ENDPOINTS:
        url = f"https://{domain}{ep}"
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                # Basic parsing for Name and Position
                # Looking for patterns like <h3>Name</h3><span>Position</span>
                # or similar.
                
                # Regex for emails
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resp.text)
                if not emails: continue
                
                # Find lines containing emails
                lines = resp.text.split('\n')
                for line in lines:
                    found_email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                    if found_email:
                        email = found_email.group(0)
                        # Try to extract name/position from surrounding tags
                        clean_line = re.sub('<[^<]+?>', '', line).strip()
                        if email in clean_line:
                            name_pos = clean_line.replace(email, "").strip()
                            # Basic split attempt
                            parts = name_pos.split('-') if '-' in name_pos else [name_pos]
                            results.append({
                                "Name": parts[0].strip() or "Unknown",
                                "Email": email,
                                "Position": parts[1].strip() if len(parts) > 1 else "Staff"
                            })
                if results: break # Found a working directory
        except:
            continue
            
    # Heuristics if no directory found
    if not results:
        results.append({"Name": "General Contact", "Email": f"info@{domain}", "Position": "Inquiry"})
        
    return results

def main():
    final_leads = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(hunt_staff, d): d for d in DOMAINS}
        for future in concurrent.futures.as_completed(futures):
            final_leads.extend(future.result())

    output_path = "/root/ai-workforce-os/output/marketing/automated_leads_v1.csv"
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Email", "Position"])
        writer.writeheader()
        writer.writerows(final_leads)
    
    print(f"Captured {len(final_leads)} leads to {output_path}")

if __name__ == "__main__":
    main()
