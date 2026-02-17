import asyncio
import csv
import re
import sys
import logging
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass

import aiodns
import aiofiles

# Elite Brand Colors
GOLD = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Institutional Standards for Email Validation
REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
DEFAULT_SENDER = "verify@example.com"


@dataclass
class ValidationResult:
    email: str
    status: str
    mx: str
    provider: str = "Unknown"
    spoofable: str = "N/A"
    smtp_code: Optional[int] = None
    smtp_message: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "email": self.email,
            "status": self.status,
            "mx": self.mx,
            "provider": self.provider,
            "spoofable": self.spoofable,
            "smtp_code": str(self.smtp_code) if self.smtp_code else "N/A",
            "smtp_message": self.smtp_message,
        }


class EmailValidator:
    """Institutional standards for high-performance email validation."""

    def __init__(self, concurrency: int = 100, sender: str = DEFAULT_SENDER):
        self.resolver = aiodns.DNSResolver()
        self.semaphore = asyncio.Semaphore(concurrency)
        self.sender = sender

    def check_syntax(self, email: str) -> bool:
        """Validate email format using institutional regex standards."""
        return re.match(REGEX, email) is not None

    async def get_mx_records(self, domain: str) -> List[str]:
        """Query DNS for MX records of a given domain."""
        try:
            records = await self.resolver.query(domain, "MX")
            return [str(record.host) for record in records]
        except Exception:
            return []

    def get_provider(self, mx_hosts: List[str]) -> str:
        """Identify the domain provider based on MX records."""
        if not mx_hosts:
            return "None"

        mx_string = " ".join(mx_hosts).lower()
        if "google.com" in mx_string or "googlemail.com" in mx_string:
            return "Google"
        if (
            "outlook.com" in mx_string
            or "hotmail.com" in mx_string
            or "microsoft.com" in mx_string
        ):
            return "Microsoft"
        if "yahoodns.net" in mx_string:
            return "Yahoo"
        if "icloud.com" in mx_string:
            return "Apple"
        if "zoho.com" in mx_string:
            return "Zoho"
        if "secureserver.net" in mx_string:
            return "GoDaddy"
        return "Custom/Other"

    async def check_spoofable(self, domain: str) -> str:
        """Check SPF and DMARC records to determine if a domain is spoofable."""
        spf_exists = False
        dmarc_exists = False
        weak_spf = False
        weak_dmarc = False

        try:
            # Check SPF
            txt_records = await self.resolver.query(domain, "TXT")
            for record in txt_records:
                txt_content = str(record.text).lower()
                if "v=spf1" in txt_content:
                    spf_exists = True
                    # Weak SPF: ends with +all or ?all, or doesn't have -all/~all
                    if "+all" in txt_content or "?all" in txt_content:
                        weak_spf = True
                    elif "~all" not in txt_content and "-all" not in txt_content:
                        weak_spf = True

            # Check DMARC
            try:
                dmarc_records = await self.resolver.query(f"_dmarc.{domain}", "TXT")
                for record in dmarc_records:
                    txt_content = str(record.text).lower()
                    if "v=dmarc1" in txt_content:
                        dmarc_exists = True
                        if "p=none" in txt_content:
                            weak_dmarc = True
            except:
                pass  # DMARC record query failed

            if not spf_exists or not dmarc_exists:
                return "Yes (Missing Records)"
            if weak_spf or weak_dmarc:
                return "Yes (Weak Policy)"

            return "No"
        except Exception:
            return "Unknown"

    async def verify_smtp(self, email: str, mx_host: str) -> tuple[Optional[int], str]:
        """Perform deep validation by establishing an SMTP connection."""
        reader, writer = None, None
        try:
            # Connect to SMTP server on port 25
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(mx_host, 25), timeout=10
            )

            async def get_response():
                line = await reader.readline()
                if not line:
                    return None, "No response"
                content = line.decode().strip()
                code = int(content[:3])
                return code, content[4:]

            # Read initial banner
            code, msg = await get_response()
            if code != 220:
                return code, f"Banner Error: {msg}"

            # EHLO
            writer.write(f"EHLO {mx_host}\r\n".encode())
            await writer.drain()
            code, msg = await get_response()

            # Handle multi-line EHLO responses
            while msg.startswith("-") or (
                reader.at_eof() is False and reader._buffer.startswith(b"250-")
            ):
                line = await reader.readline()
                if not line:
                    break

            if code != 250:
                return code, f"EHLO Error: {msg}"

            # MAIL FROM
            writer.write(f"MAIL FROM:<{self.sender}>\r\n".encode())
            await writer.drain()
            code, msg = await get_response()
            if code != 250:
                return code, f"MAIL FROM Error: {msg}"

            # RCPT TO
            writer.write(f"RCPT TO:<{email}>\r\n".encode())
            await writer.drain()
            code, msg = await get_response()

            return code, msg

        except asyncio.TimeoutError:
            return None, "Connection Timeout"
        except Exception as e:
            return None, f"Connection Failed: {str(e)}"
        finally:
            if writer:
                writer.close()
                try:
                    await writer.wait_closed()
                except:
                    pass

    async def validate_email(self, email: str) -> ValidationResult:
        """Perform full validation including syntax, MX lookup, and SMTP verification."""
        async with self.semaphore:
            email = email.strip().lower()
            status = "Invalid Syntax"
            mx_hosts = []
            smtp_code = None
            smtp_msg = ""

            if self.check_syntax(email):
                parts = email.split("@")
                if len(parts) == 2:
                    domain = parts[1]
                    mx_hosts = await self.get_mx_records(domain)
                    provider = self.get_provider(mx_hosts)
                    spoofable = await self.check_spoofable(domain)

                    if mx_hosts:
                        status = "Valid (MX Found)"
                        # Attempt SMTP verification on the primary MX record
                        for mx in mx_hosts[:1]:  # Try primary MX
                            code, msg = await self.verify_smtp(email, mx)
                            smtp_code = code
                            smtp_msg = msg
                            if code == 250:
                                status = "Valid (SMTP Verified)"
                            elif code in [550, 551, 554]:
                                status = "Invalid Recipient (SMTP Rejected)"
                            elif code:
                                status = f"SMTP Warning ({code})"
                            else:
                                status = f"SMTP Failed: {msg}"
                    else:
                        status = "Invalid Domain (No MX)"
                else:
                    status = "Invalid Format"
                    provider = "N/A"
                    spoofable = "N/A"

            return ValidationResult(
                email=email,
                status=status,
                mx=", ".join(mx_hosts) if mx_hosts else "N/A",
                provider=provider,
                spoofable=spoofable,
                smtp_code=smtp_code,
                smtp_message=smtp_msg,
            )


async def process_list(
    input_path: str,
    output_path: str,
    concurrency: int,
    sender: str,
    batch_size: int = 50,
):
    """Orchestrate the validation process for a list of emails with batch processing."""
    validator = EmailValidator(concurrency=concurrency, sender=sender)
    is_csv = input_path.lower().endswith(".csv")

    header_written = False
    count = 0
    valid_count = 0
    total_emails = 0

    # First, let's count total if possible, or just process
    # For now, let's just process it to avoid double reading large files

    print(f"{GOLD}[*] Starting validation for {input_path}...{RESET}")
    print(f"{CYAN}[*] Concurrency: {concurrency} | Batch Size: {batch_size}{RESET}")

    try:

        async def handle_batch(batch_data, writer, csvfile):
            nonlocal valid_count, count
            tasks = [validator.validate_email(email) for email, _ in batch_data]
            results = await asyncio.gather(*tasks)

            for i, result in enumerate(results):
                res_dict = result.to_dict()
                if is_csv:
                    row = batch_data[i][1].copy()
                    row.update(
                        {
                            "validation_status": res_dict["status"],
                            "mx_records": res_dict["mx"],
                            "provider": res_dict["provider"],
                            "spoofable": res_dict["spoofable"],
                            "smtp_code": res_dict["smtp_code"],
                            "smtp_message": res_dict["smtp_message"],
                        }
                    )
                    writer.writerow(row)
                else:
                    writer.writerow(res_dict)

                count += 1
                if "Valid" in result.status:
                    valid_count += 1

            csvfile.flush()
            print(f"[*] Progress: {count} processed | Valid: {valid_count}", end="\r")

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = None

            if is_csv:
                with open(input_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    if not fieldnames:
                        print(
                            f"{RED}[!] CSV file is empty or has no headers: {input_path}{RESET}"
                        )
                        return

                    email_col = next(
                        (col for col in fieldnames if "email" in col.lower()),
                        fieldnames[0],
                    )

                    # Prepare output header
                    header_fields = list(fieldnames)
                    for col in [
                        "validation_status",
                        "mx_records",
                        "provider",
                        "spoofable",
                        "smtp_code",
                        "smtp_message",
                    ]:
                        if col not in header_fields:
                            header_fields.append(col)

                    writer = csv.DictWriter(csvfile, fieldnames=header_fields)
                    writer.writeheader()

                    batch = []
                    for row in reader:
                        email = row.get(email_col, "").strip()
                        if email:
                            batch.append((email, row))
                            if len(batch) >= batch_size:
                                await handle_batch(batch, writer, csvfile)
                                batch = []
                    if batch:
                        await handle_batch(batch, writer, csvfile)
            else:
                async with aiofiles.open(input_path, mode="r") as f:
                    fieldnames = [
                        "email",
                        "status",
                        "mx",
                        "provider",
                        "spoofable",
                        "smtp_code",
                        "smtp_message",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    batch = []
                    async for line in f:
                        line = line.strip()
                        if line and "@" in line:
                            batch.append((line, None))
                            if len(batch) >= batch_size:
                                await handle_batch(batch, writer, csvfile)
                                batch = []
                    if batch:
                        await handle_batch(batch, writer, csvfile)

        print("\n")
        print(f"{GREEN}[!] Validation complete.{RESET}")
        print(f"{GOLD}[+] Results stored in: {output_path}{RESET}")
        print(f"{CYAN}[+] Valid: {valid_count} | Total: {count}{RESET}")

    except FileNotFoundError:
        print(f"{RED}[!] Input file not found: {input_path}{RESET}")
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Professional-grade Email Validator")
    parser.add_argument("input", nargs="?", help="Path to input file (.txt or .csv)")
    parser.add_argument(
        "-i",
        "--input",
        "--input-file",
        dest="input_alt",
        help="Path to input file (.txt or .csv)",
    )
    parser.add_argument(
        "-o", "--output", default="validated_emails.csv", help="Output CSV path"
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=100,
        help="Number of concurrent DNS lookups",
    )
    parser.add_argument(
        "-s",
        "--sender",
        "--from",
        dest="sender",
        default=DEFAULT_SENDER,
        help="Sender email for SMTP verification",
    )

    args = parser.parse_args()

    input_path = args.input_alt or args.input
    if not input_path:
        parser.error(
            "The input file is required (either as positional argument or via --input-file)"
        )

    output_path = args.output
    if output_path == "validated_emails.csv":
        import os
        from datetime import datetime

        base_name = os.path.splitext(os.path.basename(input_path))[0]
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = f"{base_name}_result_{date_str}.csv"

    try:
        asyncio.run(
            process_list(input_path, output_path, args.concurrency, args.sender)
        )
    except KeyboardInterrupt:
        print(f"\n{RED}[!] Process interrupted by user.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
