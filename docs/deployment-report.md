# Deployment Report

## Environment
- Docker Engine: 29.5.3
- Compose: v5.1.4
- Host ports in use: 80, 8000, 3000
- Compose ports planned: 80, 3000

## Status
- Compose project validated and repaired.
- Repo committed/pushed.

## Blocking issue
- Port 80 on the host is already bound by live Nginx. Deploying Compose would collide and is not begun without user direction.
- If testing, stop the live Nginx first.
