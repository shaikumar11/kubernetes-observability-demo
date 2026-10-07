#!/usr/bin/env bash
# Creates a local kind cluster and deploys the app and monitoring stack.
set -euo pipefail
cd "$(dirname "$0")/.."

kind create cluster --name demo --config k8s/kind-config.yaml

docker build -t demo-app:1.0.0 .
kind load docker-image demo-app:1.0.0 --name demo

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/configmap.yaml -f k8s/redis-statefulset.yaml
kubectl rollout status statefulset/redis -n demo --timeout=120s
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
kubectl rollout status deployment/demo-app -n demo --timeout=120s
kubectl apply -f k8s/monitoring/
kubectl rollout status deployment/prometheus -n monitoring --timeout=120s
kubectl rollout status deployment/grafana -n monitoring --timeout=120s

echo "App:        http://localhost:8080/docs"
echo "Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "Grafana:    kubectl port-forward -n monitoring svc/grafana 3000:3000"
