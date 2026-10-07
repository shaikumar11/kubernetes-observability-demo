# Kubernetes Deployment with Monitoring

A containerized FastAPI service deployed to a local Kubernetes cluster with kind, with a Redis StatefulSet, an ingress, health probes, rolling updates and a Prometheus and Grafana monitoring stack. Everything runs on your laptop.

## What it shows

- Deployment with two replicas, resource requests and limits, readiness and liveness probes, and a zero downtime rolling update.
- Service and Ingress, so traffic enters through nginx on http://localhost:8080.
- Redis as a StatefulSet with a headless service and a persistent volume claim, used by the `/visits` counter.
- ConfigMap for configuration.
- Prometheus scraping the `/metrics` endpoint, with two alert rules.
- Grafana connected to Prometheus.
- Optional HorizontalPodAutoscaler in `k8s/optional`.

## Structure

- `app/`: service with `/health`, `/ready`, `/work`, `/visits`, `/metrics`. `tests/`: pytest tests.
- `k8s/`: manifests. `k8s/monitoring/`: Prometheus and Grafana.
- `scripts/up.sh`, `down.sh`, `load.sh`: create the cluster, remove it, generate traffic.

## Prerequisites

Docker, kind, kubectl.

## Run it

```bash
./scripts/up.sh
curl localhost:8080/health
curl localhost:8080/visits     # run twice
```

Check the objects:

```bash
kubectl get pods,svc,ingress -n demo
kubectl get statefulset,pvc -n demo
kubectl get pods -n monitoring
```

Generate traffic and open the monitoring tools:

```bash
./scripts/load.sh &
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
```

In Prometheus at http://localhost:9090 open Alerts and wait for HighErrorRate to fire. In Grafana at http://localhost:3000 create a dashboard with these queries:

- Request rate: `sum(rate(http_requests_total[1m]))`
- Error ratio: `sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))`
- p95 latency: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))`

## Practice troubleshooting

```bash
kubectl delete pod -n demo -l app=demo-app          # pods are recreated
kubectl delete pod redis-0 -n demo                  # visit count survives the restart
kubectl logs -n demo deploy/demo-app
kubectl describe pod -n demo -l app=demo-app
kubectl set image deploy/demo-app demo-app=demo-app:does-not-exist -n demo   # watch a failed rollout
kubectl rollout undo deploy/demo-app -n demo         # roll back
kubectl apply -f k8s/optional/hpa.yaml               # needs metrics-server
```

Clean up with `./scripts/down.sh`.

## Run the service without Kubernetes

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
flake8 app tests && pytest -q
uvicorn app.main:app --reload
```

## Things to explain in an interview

- **Pod, Deployment, Service, Ingress**: pods run containers, a Deployment keeps the wanted number running and handles updates, a Service gives a stable address, an Ingress routes outside traffic.
- **Readiness and liveness**: readiness decides if a pod gets traffic, liveness decides if it is restarted.
- **Rolling update**: maxUnavailable 0 and maxSurge 1 start a new pod before removing an old one.
- **StatefulSet**: gives Redis a stable name and its own volume, unlike a Deployment where pods are interchangeable.
- **Requests and limits**: requests help the scheduler place pods, limits cap usage.
- **Prometheus**: pulls metrics from `/metrics`. Counters and histograms produce rate, error ratio and percentile latency queries.
- **Alert rule**: HighErrorRate fires when more than 20 percent of requests fail for one minute.
- **Limitations and next steps**: a single Redis replica is not highly available, Grafana runs without login for the demo, and a real cluster would use Helm charts, Alertmanager and Terraform managed EKS.
