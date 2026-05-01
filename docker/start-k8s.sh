#!/bin/bash

set -e

echo "🚀 Starting Kubernetes cluster in container..."

# Create kubeconfig directory
mkdir -p kubeconfig

# Start K3s cluster
docker-compose -f k8s-compose.yml up -d

echo "⏳ Waiting for Kubernetes cluster to start..."
sleep 30

# Wait for kubeconfig to be generated
for i in {1..60}; do
    if [ -f "kubeconfig/kubeconfig.yaml" ]; then
        echo "✅ Kubernetes cluster is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Kubernetes cluster failed to start"
        exit 1
    fi
    sleep 2
done

# Copy kubeconfig to user's home
mkdir -p ~/.kube
cp kubeconfig/kubeconfig.yaml ~/.kube/config
chmod 600 ~/.kube/config

echo "🔧 Kubernetes cluster is running!"
echo "📋 Cluster info:"
echo "   - API Server: https://localhost:6443"
echo "   - Kubeconfig: ~/.kube/config"
echo ""
echo "🛑 To stop cluster: ./stop-k8s.sh" 