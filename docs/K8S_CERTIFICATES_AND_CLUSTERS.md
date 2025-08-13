# 🔐 Kubernetes Certificates and Cluster Management

Полное руководство по управлению сертификатами и кластерами Kubernetes через MCP сервер `ai-admin`.

## 📋 Содержание

1. [Создание кластеров с сертификатами](#создание-кластеров-с-сертификатами)
2. [Управление сертификатами](#управление-сертификатами)
3. [Аутентификация клиентов](#аутентификация-клиентов)
4. [Тестирование команд](#тестирование-команд)
5. [Примеры использования](#примеры-использования)

## 🚀 Создание кластеров с сертификатами

### Команда `k8s_cluster_setup`

Универсальная команда для создания полных Kubernetes кластеров с автоматической настройкой сертификатов.

```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "my-production-cluster",
    "cluster_type": "kind",
    "admin_user": "kubernetes-admin",
    "admin_organization": "system:masters",
    "namespace": "production",
    "wait_timeout": 300,
    "cluster_config": {
      "workers": 2,
      "kubernetes_version": "1.28.0"
    },
    "cert_config": {
      "key_size": 4096,
      "days_valid": 365
    }
  }
}
```

**Поддерживаемые типы кластеров:**
- `kind` - Kubernetes in Docker (рекомендуется для разработки)
- `k3s` - Легковесный Kubernetes
- `minikube` - Локальный Kubernetes

**Автоматически создаваемые сертификаты:**
- CA (Certificate Authority)
- kubernetes-admin (администратор)
- system:node:localhost (kubelet)
- system:kube-controller-manager
- system:kube-scheduler
- kubernetes.default.svc.cluster.local (API server)

### Примеры создания кластеров

#### Kind кластер для разработки
```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "dev-cluster",
    "cluster_type": "kind",
    "admin_user": "developer",
    "namespace": "development",
    "cluster_config": {
      "workers": 1,
      "kubernetes_version": "1.28.0"
    }
  }
}
```

#### K3s кластер для продакшена
```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "prod-cluster",
    "cluster_type": "k3s",
    "admin_user": "admin",
    "namespace": "production",
    "cluster_config": {
      "port": 6443
    },
    "cert_config": {
      "key_size": 4096,
      "days_valid": 730
    }
  }
}
```

## 🔐 Управление сертификатами

### Команда `k8s_certificates`

Управление сертификатами для Kubernetes кластеров.

#### Создание сертификатов

```json
{
  "command": "k8s_certificates",
  "params": {
    "action": "create",
    "cluster_name": "my-cluster",
    "cert_type": "client",
    "common_name": "developer-user",
    "organization": "system:developers",
    "key_size": 2048,
    "days_valid": 365
  }
}
```

#### Настройка полной инфраструктуры сертификатов

```json
{
  "command": "k8s_certificates",
  "params": {
    "action": "setup_cluster",
    "cluster_name": "my-cluster",
    "common_name": "kubernetes-admin",
    "organization": "system:masters",
    "key_size": 4096,
    "days_valid": 365
  }
}
```

#### Создание конфигурации клиента

```json
{
  "command": "k8s_certificates",
  "params": {
    "action": "create_client_config",
    "cluster_name": "my-cluster",
    "common_name": "kubernetes-admin",
    "organization": "system:masters",
    "server_url": "https://localhost:6443"
  }
}
```

#### Проверка сертификатов

```json
{
  "command": "k8s_certificates",
  "params": {
    "action": "verify",
    "cluster_name": "my-cluster",
    "cert_type": "kubernetes-admin"
  }
}
```

#### Список сертификатов

```json
{
  "command": "k8s_certificates",
  "params": {
    "action": "list",
    "cluster_name": "my-cluster"
  }
}
```

## 🔑 Аутентификация клиентов

### Структура сертификатов

```
certificates/
└── my-cluster/
    ├── kubernetes-ca-my-cluster.crt      # CA сертификат
    ├── kubernetes-ca-my-cluster.key      # CA приватный ключ
    ├── kubernetes-admin.crt              # Админ сертификат
    ├── kubernetes-admin.key              # Админ приватный ключ
    ├── system:node:localhost.crt         # Kubelet сертификат
    ├── system:node:localhost.key         # Kubelet приватный ключ
    └── ...

kubeconfigs/
└── my-cluster/
    └── kubeconfig.yaml                   # Конфигурация клиента
```

### Автоматическая настройка аутентификации

Все команды Kubernetes автоматически используют правильные сертификаты:

1. **Определение кластера** - по имени кластера
2. **Загрузка kubeconfig** - из `./kubeconfigs/{cluster_name}/kubeconfig.yaml`
3. **Настройка сертификатов** - из `./certificates/{cluster_name}/`
4. **Аутентификация** - с использованием клиентских сертификатов

### Роли и разрешения

**system:masters** - Полные права администратора
```json
{
  "organization": "system:masters"
}
```

**system:developers** - Права разработчика
```json
{
  "organization": "system:developers"
}
```

**system:nodes** - Права для узлов кластера
```json
{
  "organization": "system:nodes"
}
```

## 🧪 Тестирование команд

### Запуск тестов

```bash
# Запуск полного теста всех команд
python scripts/test_k8s_commands.py

# Проверка конкретного кластера
python scripts/test_k8s_commands.py --cluster my-cluster
```

### Что тестируется

1. ✅ Создание кластера с сертификатами
2. ✅ Управление сертификатами
3. ✅ Операции с namespace
4. ✅ Создание и управление подами
5. ✅ Создание деплойментов
6. ✅ Создание сервисов
7. ✅ Мониторинг и отладка
8. ✅ Очистка ресурсов

### Проверка статуса кластера

```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "status",
    "cluster_name": "my-cluster",
    "cluster_type": "kind"
  }
}
```

### Тестирование подключения

```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "test",
    "cluster_name": "my-cluster"
  }
}
```

## 📝 Примеры использования

### Полный workflow создания кластера

```json
// 1. Создать кластер с сертификатами
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "production",
    "cluster_type": "kind",
    "admin_user": "admin",
    "namespace": "production"
  }
}

// 2. Создать namespace для приложения
{
  "command": "k8s_namespace_create",
  "params": {
    "namespace": "my-app",
    "labels": {
      "environment": "production",
      "team": "backend"
    }
  }
}

// 3. Создать ConfigMap с настройками
{
  "command": "k8s_configmap_create",
  "params": {
    "configmap_name": "app-config",
    "data": {
      "database.host": "postgres",
      "database.port": "5432",
      "app.environment": "production"
    },
    "namespace": "my-app"
  }
}

// 4. Создать Secret с паролями
{
  "command": "k8s_secret_create",
  "params": {
    "secret_name": "app-secrets",
    "data": {
      "database.password": "secret123",
      "api.key": "api_key_value"
    },
    "namespace": "my-app"
  }
}

// 5. Создать Deployment
{
  "command": "k8s_deployment_create",
  "params": {
    "project_path": "/home/user/my-app",
    "replicas": 3,
    "namespace": "my-app",
    "cpu_limit": "500m",
    "memory_limit": "1Gi"
  }
}

// 6. Создать Service
{
  "command": "k8s_service_create",
  "params": {
    "service_type": "LoadBalancer",
    "namespace": "my-app",
    "port": 80
  }
}
```

### Управление несколькими кластерами

```json
// Создать кластер для разработки
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "dev",
    "cluster_type": "kind",
    "admin_user": "developer"
  }
}

// Создать кластер для тестирования
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "staging",
    "cluster_type": "k3s",
    "admin_user": "tester"
  }
}

// Создать продакшн кластер
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "create",
    "cluster_name": "production",
    "cluster_type": "kind",
    "admin_user": "admin",
    "cert_config": {
      "key_size": 4096,
      "days_valid": 730
    }
  }
}
```

### Мониторинг и отладка

```json
// Проверить статус всех кластеров
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "status",
    "cluster_name": "production"
  }
}

// Получить логи приложения
{
  "command": "k8s_logs",
  "params": {
    "namespace": "my-app",
    "lines": 100,
    "since": "1h"
  }
}

// Выполнить команду в поде
{
  "command": "k8s_exec",
  "params": {
    "command": "ps aux",
    "namespace": "my-app"
  }
}

// Проверить статус подов
{
  "command": "k8s_pod_status",
  "params": {
    "namespace": "my-app",
    "all_ai_admin": true
  }
}
```

## 🛠️ Требования

### Системные требования

- **kubectl** - для взаимодействия с Kubernetes
- **kind** - для создания локальных кластеров
- **openssl** - для генерации сертификатов
- **docker** - для контейнеров (для kind и k3s)

### Установка зависимостей

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y kubectl kind openssl docker.io

# CentOS/RHEL
sudo yum install -y kubectl kind openssl docker

# macOS
brew install kubectl kind openssl docker
```

### Проверка установки

```bash
# Проверить kubectl
kubectl version --client

# Проверить kind
kind version

# Проверить openssl
openssl version

# Проверить docker
docker --version
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Размер ключей**: Используйте 4096 бит для продакшена
2. **Срок действия**: Устанавливайте разумные сроки (365-730 дней)
3. **Хранение**: Храните приватные ключи в безопасном месте
4. **Ротация**: Регулярно обновляйте сертификаты
5. **Доступ**: Ограничивайте доступ к сертификатам

### Удаление кластера

```json
{
  "command": "k8s_cluster_setup",
  "params": {
    "action": "delete",
    "cluster_name": "my-cluster",
    "cluster_type": "kind"
  }
}
```

**Примечание**: Удаление кластера также удаляет все сертификаты и конфигурации.

## 📊 Мониторинг и логирование

### Структура логов

```
logs/
├── k8s_cluster_setup.log
├── k8s_certificates.log
└── k8s_operations.log
```

### Отладка проблем

1. **Проверить статус кластера**
2. **Проверить сертификаты**
3. **Проверить логи**
4. **Проверить подключение**

```bash
# Проверить все кластеры
python scripts/test_k8s_commands.py --status-only

# Проверить конкретный кластер
python scripts/test_k8s_commands.py --cluster my-cluster --test connection
```

Теперь у тебя есть **полная система управления Kubernetes кластерами с сертификатами**! 🚀 