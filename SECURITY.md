# Production Security Configuration for Mina Platform

## Content Security Policy (CSP)

Add the following Content Security Policy header to your web server configuration for enhanced security:

### Recommended CSP (Development-friendly)
```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.replit.com;
  connect-src 'self' wss: ws: https://api.openai.com;
  img-src 'self' data: https:;
  font-src 'self' https://cdnjs.cloudflare.com;
  frame-ancestors 'none';
  base-uri 'self';
  object-src 'none';
  upgrade-insecure-requests;
```

### Strict CSP (Enhanced Security)
```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net;
  style-src 'self' https://cdnjs.cloudflare.com https://cdn.replit.com;
  connect-src 'self' wss: ws: https://api.openai.com;
  img-src 'self' data: https:;
  font-src 'self' https://cdnjs.cloudflare.com;
  frame-ancestors 'none';
  base-uri 'self';
  object-src 'none';
  upgrade-insecure-requests;
```

**Note:** The strict CSP requires removing all inline scripts and styles. Use the recommended CSP initially and gradually migrate to strict CSP after auditing inline content.

## Essential Security Headers

Add these headers to your production web server configuration:

```
# HTTPS Security
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# Content Type Protection
X-Content-Type-Options: nosniff

# Frame Protection
X-Frame-Options: DENY

# XSS Protection
X-XSS-Protection: 1; mode=block

# Permissions Policy (Feature Control)
Permissions-Policy: geolocation=(), microphone=(self), camera=(), payment=(), usb=()

# Referrer Protection
Referrer-Policy: strict-origin-when-cross-origin

# Cross-Origin Policy
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
```

## Subresource Integrity (SRI)

All CDN assets in the application include SRI hashes for integrity verification:

- **Font Awesome 6.4.0**: `sha512-iecdLmaskl7CVkqkXNQ/ZH/XLlvWZOJyj7Yy7tcenmpD1ypASozpmT/E0iPtmFIB46ZmdtAc9eNBvH0H/ZpiBw==`
- **Socket.IO 4.7.2**: `sha512-zoJXRvW2gC8Z0Xo3lBbao5+AS3g6YWr5ztKqaWp5GTjvwSlk/YBP47O58GxnMg0D45hVddEc3Qg6NM1oSf8yig==`
- **Bootstrap 5.3.2**: `sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL`

## Implementation Guide

### For Nginx:
```nginx
server {
    # Add security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Permissions-Policy "geolocation=(), microphone=(self), camera=()" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Content Security Policy
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.replit.com; connect-src 'self' wss: ws: https://api.openai.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests;" always;
}
```

### For Apache:
```apache
<IfModule mod_headers.c>
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Permissions-Policy "geolocation=(), microphone=(self), camera=()"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.replit.com; connect-src 'self' wss: ws: https://api.openai.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests;"
</IfModule>
```

### For Flask Application:
```python
from flask import Flask

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(self), camera=()'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.replit.com; connect-src 'self' wss: ws: https://api.openai.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; upgrade-insecure-requests;"
    return response
```

## Security Checklist

- [ ] All CDN assets include SRI hashes ✅
- [ ] CSP header configured for production
- [ ] HTTPS enforced with HSTS
- [ ] XSS protection enabled
- [ ] Content-Type sniffing disabled
- [ ] Frame embedding disabled
- [ ] Permissions policy configured
- [ ] Referrer policy set to strict-origin-when-cross-origin
- [ ] Cross-origin policies configured for enhanced isolation

## Monitoring & Validation

Use the following tools to validate your security configuration:

1. **Mozilla Observatory**: https://observatory.mozilla.org/
2. **Security Headers**: https://securityheaders.com/
3. **CSP Evaluator**: https://csp-evaluator.withgoogle.com/
4. **SSL Labs**: https://www.ssllabs.com/ssltest/

## Important Notes

- Test CSP in report-only mode first: `Content-Security-Policy-Report-Only`
- Monitor CSP violation reports to identify necessary adjustments
- Regularly update SRI hashes when upgrading CDN dependencies
- Review and update security headers periodically
- Consider implementing Certificate Authority Authorization (CAA) DNS records