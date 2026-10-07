#!/usr/bin/env bash
# Sends traffic with some failures so graphs and the alert have data.
for i in $(seq 1 300); do
  curl -s -o /dev/null "http://localhost:8080/work?fail_rate=0.4&delay_ms=100"
  curl -s -o /dev/null "http://localhost:8080/visits"
  sleep 0.2
done
