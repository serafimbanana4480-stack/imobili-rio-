# Cloudflare Tunnel Setup for HTTPS

This guide explains how to set up free HTTPS using Cloudflare Tunnel for the Real Estate AI platform.

## Why Cloudflare Tunnel?

- **Free**: No cost for basic usage
- **Easy**: Simple setup without server configuration
- **Secure**: Automatic HTTPS with valid SSL certificates
- **No Port Forwarding**: Works behind NAT/firewall
- **Dynamic DNS**: No need for static IP

## Prerequisites

1. Cloudflare account (free)
2. Domain registered with Cloudflare (or use Cloudflare's free subdomain)
3. Windows machine with the platform installed

## Installation Steps

### 1. Install cloudflared

Download cloudflared for Windows:
```bash
# Download from: https://github.com/cloudflare/cloudflared/releases/latest
# Or use winget:
winget install Cloudflare.cloudflared
```

### 2. Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will open a browser to authenticate with your Cloudflare account.

### 3. Create a Tunnel

```bash
cloudflared tunnel create realestate-ai
```

Save the tunnel ID that is returned.

### 4. Configure the Tunnel

Create configuration file `C:\Users\<username>\.cloudflared\config.yml`:

```yaml
tunnel: <tunnel-id>
credentials-file: C:\Users\<username>\.cloudflared\<tunnel-id>.json

ingress:
  # API endpoint
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  
  # Dashboard endpoint
  - hostname: dashboard.yourdomain.com
    service: http://localhost:8501
  
  # Catch-all service (optional)
  - service: http_status:404
```

### 5. Set Up DNS Records

```bash
cloudflared tunnel route dns realestate-ai api.yourdomain.com
cloudflared tunnel route dns realestate-ai dashboard.yourdomain.com
```

### 6. Start the Tunnel

```bash
cloudflared tunnel run realestate-ai
```

### 7. Run as Service (Windows)

To run the tunnel automatically on startup:

```bash
# Install as Windows service
cloudflared service install

# Start the service
cloudflared service start
```

## Alternative: Using Cloudflare Free Subdomain

If you don't have a domain, Cloudflare provides free subdomains:

1. After `cloudflared tunnel login`, you'll get a free subdomain like `your-name.pages.dev`
2. Configure the tunnel to use this subdomain
3. No DNS setup required

## Testing

Once the tunnel is running:

1. Start the API server: `cd realestate_engine && ../venv312/Scripts/python.exe -m api.main`
2. Start the dashboard: `cd realestate_engine/dashboard && streamlit run app.py`
3. Access via HTTPS:
   - API: `https://api.yourdomain.com/api/v1/health/`
   - Dashboard: `https://dashboard.yourdomain.com`

## Troubleshooting

### Tunnel won't start
- Check if cloudflared is installed correctly
- Verify credentials file exists
- Check if ports 8000 and 8501 are available

### Can't access HTTPS
- Verify DNS records are set correctly
- Check Cloudflare dashboard for tunnel status
- Ensure API and dashboard are running locally

### Certificate errors
- Cloudflare provides valid certificates automatically
- Clear browser cache if seeing old certificates
- Wait 5-10 minutes for DNS propagation

## For Sale Deployment

When selling the system to a client:

1. Provide this guide to the client
2. Help them set up Cloudflare account if needed
3. Configure the tunnel for their domain
4. Test HTTPS access
5. Document the tunnel configuration for their records

## Notes

- Cloudflare Tunnel is free for personal use
- Commercial use may require paid plan (check Cloudflare pricing)
- Tunnel must be running for HTTPS to work
- Consider setting up automatic startup for production use
