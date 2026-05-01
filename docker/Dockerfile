FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        docker.io \
        curl \
        git \
        wget \
        gnupg \
        lsb-release \
        software-properties-common \
        procps \
        sudo \
        pciutils \
        lshw \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install NVIDIA Container Toolkit
RUN curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
    apt-get update && \
    apt-get install -y nvidia-container-toolkit && \
    rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl-original && \
    kubectl-original version --client

# Create kubectl wrapper for proper cluster connection
RUN echo '#!/bin/bash' > /usr/local/bin/kubectl && \
    echo 'kubectl-original --kubeconfig=/home/appuser/.kube/config --insecure-skip-tls-verify "$@"' >> /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Install Ollama properly
RUN curl -fsSL https://ollama.ai/install.sh | sh && \
    ln -sf /usr/local/bin/ollama /usr/bin/ollama

# Create app user and group
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser && \
    usermod -aG docker appuser && \
    usermod -aG video appuser

# Create directories and set permissions
RUN mkdir -p /app/config /app/logs /app/cache /app/models /home/appuser/.ollama /home/appuser/.kube && \
    chown -R appuser:appuser /app /home/appuser/.ollama /home/appuser/.kube

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create comprehensive startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== AI Admin Server Startup ==="\n\
\n\
# Set environment variables\n\
export OLLAMA_HOST=0.0.0.0\n\
export OLLAMA_ORIGINS=*\n\
export OLLAMA_MODELS=/app/models\n\
export OLLAMA_HOME=/home/appuser/.ollama\n\
\n\
# Create necessary directories with proper permissions\n\
echo "Setting up directories..."\n\
mkdir -p /home/appuser/.ollama /app/models /home/appuser/.kube\n\
chown -R appuser:appuser /home/appuser/.ollama /app/models\n\
\n\
# Check kubectl installation\n\
echo "Checking kubectl..."\n\
if command -v kubectl &> /dev/null; then\n\
    echo "✅ kubectl is installed: $(kubectl version --client --short)"\n\
    # Check if we can connect to host cluster\n\
    if [ -f "/home/appuser/.kube/config" ]; then\n\
        echo "✅ kubectl config found, checking cluster connection..."\n\
        if kubectl cluster-info &> /dev/null; then\n\
            echo "✅ Connected to Kubernetes cluster"\n\
        else\n\
            echo "⚠️  kubectl config found but cannot connect to cluster"\n\
        fi\n\
    else\n\
        echo "⚠️  No kubectl config found - will work when cluster is available"\n\
    fi\n\
else\n\
    echo "❌ kubectl not found"\n\
fi\n\
\n\
# Check Ollama installation\n\
echo "Checking Ollama..."\n\
if command -v ollama &> /dev/null; then\n\
    echo "✅ Ollama is installed: $(ollama --version)"\n\
else\n\
    echo "❌ Ollama not found"\n\
    exit 1\n\
fi\n\
\n\
# Start Ollama as appuser\n\
echo "Starting Ollama..."\n\
sudo -u appuser OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS=* ollama serve &\n\
OLLAMA_PID=$!\n\
\n\
# Wait for Ollama to start and check status\n\
echo "Waiting for Ollama to start..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then\n\
        echo "✅ Ollama started successfully on port 11434"\n\
        break\n\
    fi\n\
    if [ $i -eq 30 ]; then\n\
        echo "❌ Ollama failed to start after 30 seconds"\n\
        exit 1\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Check Ollama models\n\
echo "Checking Ollama models..."\n\
if curl -s http://localhost:11434/api/tags | grep -q "models"; then\n\
    echo "✅ Ollama models endpoint responding"\n\
else\n\
    echo "⚠️  No models found in Ollama"\n\
fi\n\
\n\
# Start the main application\n\
echo "Starting AI Admin Server..."\n\
exec python -m ai_admin.server --host 0.0.0.0 --port 8060\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set proper ownership
RUN chown -R appuser:appuser /app

# Expose ports
EXPOSE 8060 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8060/health && curl -f http://localhost:11434/api/tags || exit 1

# Start command
CMD ["/app/start.sh"] 