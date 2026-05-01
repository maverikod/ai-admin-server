#!/bin/bash

echo "🛑 Stopping Kubernetes cluster..."

# Stop K3s cluster
docker-compose -f k8s-compose.yml down

# Remove kubeconfig
rm -f ~/.kube/config

echo "✅ Kubernetes cluster stopped" 