# Custom Domain Setup

The production API is available through the custom domain:

https://themuse.space

The www subdomain redirects to the root domain:

https://www.themuse.space

The domain is connected to the Render Web Service.

DNS configuration:

- Root domain (@): A record -> 216.24.57.1
- www: CNAME -> the-muse-edit-api-luckymacy-141026-2149.onrender.com

The DNS zone is managed through NIC.UA name servers.

Render successfully verified the domain and issued an HTTPS certificate.

Secrets are not stored in Git. The .env file is excluded through .gitignore, and .env.example contains only placeholders.

Verification steps:

1. Configure DNS records in NIC.UA.
2. Verify the custom domain in Render.
3. Confirm that https://themuse.space and https://www.themuse.space open successfully.