# AT&T Modem Reboot Utility

A Python script to remotely reboot an Arris BGW210-700 modem (AT&T fiber gateway) via its HTTP management interface.

## Overview

This utility automates the process of rebooting your AT&T modem programmatically. Instead of manually logging into the web interface or using a smart plug, you can trigger a reboot from the command line or within scripts.

## Features

- ✅ Authenticate with the modem's management interface
- ✅ Extract CSRF nonces from forms for secure requests
- ✅ Validate successful reboot initiation
- ✅ Configurable modem host and password
- ✅ Environment variable support for password

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line

```bash
python reboot_modem.py --host 192.168.1.254 --password YOUR_PASSWORD
```

### With Environment Variable

Set the `MODEM_REBOOT_PASSWORD` environment variable to avoid entering the password on the command line:

```bash
export MODEM_REBOOT_PASSWORD=YOUR_PASSWORD
python reboot_modem.py
```

Or on Windows (PowerShell):
```powershell
$env:MODEM_REBOOT_PASSWORD = "YOUR_PASSWORD"
python reboot_modem.py
```

### Arguments

- `--host`: Modem hostname or IP address (default: `192.168.1.254`)
  - Supports URLs with scheme: `https://192.168.1.254` or `192.168.1.254`
- `--password`: Device password (required)
  - Can be omitted if `MODEM_REBOOT_PASSWORD` environment variable is set

## How It Works

The script follows the modem's authentication flow:

1. **Initialize session**: Obtains a SessionID cookie
2. **Request restart form**: Fetches the restart page (redirects to login if not authenticated)
3. **Extract login nonce**: Parses the HTML form to get the CSRF nonce
4. **Submit login**: Sends MD5-hashed password with nonce for authentication
5. **Get restart confirmation**: Retrieves the restart confirmation form with its nonce
6. **Submit restart request**: Posts the restart command to trigger the reboot
7. **Verify success**: Confirms the reboot was initiated by checking the response redirect

## Security Notes

- The modem uses MD5 hashing for password transmission (as implemented by the modem's firmware)
- The script uses CSRF nonces to prevent unauthorized requests
- Passwords are masked in form submissions and never logged
- Use HTTPS when available for additional security

## Troubleshooting

### "Login failed or unexpected redirect"
- Verify the password is correct
- Check that the modem is accessible at the specified host
- Ensure the modem hasn't changed its IP address

### "Could not find nonce in page"
- The modem may be in an unexpected state
- Try accessing the modem's web interface manually to verify it's responsive
- Check your network connection to the modem

## License

MIT

## Support

For issues with the AT&T modem itself, contact AT&T support. For issues with this script, check the repository.
