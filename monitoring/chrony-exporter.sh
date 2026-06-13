#!/bin/sh
# Fallback chrony metrics for Prometheus textfile collector
# Generates a metrics file if /var/spool/chrony/chrony.drift exists
OUT=/tmp/chrony-metrics.prom
[ -r /var/spool/chrony/chrony.drift ] || exit 0
DRIFT=$(awk '{print $1}' /var/spool/chrony/chrony.drift 2>/dev/null || echo 0)
cat > "$OUT" <<METRICS
# HELP chrony_drift_seconds Estimated system clock drift
# TYPE chrony_drift_seconds gauge
chrony_drift_seconds ${DRIFT}
METRICS
