#!/bin/bash
# Collect chrony clients and write to shared data directory

OUTFILE="/srv/jnop/data/ntp_status.json"
TMPFILE="${OUTFILE}.tmp"

# Get chrony clients as JSON array
CLIENTS=$(sudo chronyc clients 2>/dev/null | awk 'NR>2 && NF>0 && $1!="localhost" {
    split($0, f, " ")
    ip = f[1]
    last = f[6]
    # Determine status based on last seen (minutes)
    if (last+0 >= 60) status="crit"
    else if (last+0 >= 30) status="warn"
    else status="ok"
    # Output comma-separated if not first item
    if (NR>3) printf ","
    printf "\n    {\"Address\":\"%s\",\"Status\":\"%s\",\"NTPServer\":\"localhost\",\"Offset\":0.0,\"Reach\":377,\"Drop\":0,\"Interval\":1024}", ip, status
}')

# Write properly formatted JSON
cat > "$TMPFILE" << EOF
{
  "Clients": [$CLIENTS
  ]
}
EOF
mv "$TMPFILE" "$OUTFILE"