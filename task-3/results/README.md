# Задача 3. Распределённое планирование через Kubernetes CronJob

Результат задачи 3: локальный Minikube POC для ежедневной выгрузки аналитических данных из PostgreSQL в CSV через Kubernetes CronJob.

CronJob запускает контейнер `shipments-exporter:local` каждый день в 20:00 по московскому времени. Exporter читает таблицу `shipments` из PostgreSQL и сохраняет CSV-файл в PVC `/exports`.

## Структура

```text
task-3/results/
  exporter/
    export_shipments.py
    requirements.txt
    Dockerfile
  k8s/
    namespace.yaml
    postgres.yaml
    postgres-init-configmap.yaml
    exporter-configmap.yaml
    exporter-secret.yaml
    exports-pvc.yaml
    cronjob.yaml
  screenshots/
    .gitkeep
  README.md
```

## Требования

- Docker Desktop или Docker Engine
- Minikube
- kubectl

Внешний реестр образов не используется. Docker-образ собирается напрямую внутри Docker-демона Minikube.

## 1. Запуск Minikube

```bash
minikube start
```

Проверить состояние кластера:

```bash
minikube status
kubectl cluster-info
```

## 2. Сборка Docker-образа в Minikube

Linux/macOS/WSL:

```bash
cd task-3/results/exporter
eval $(minikube docker-env)
docker build -t shipments-exporter:local .
```

PowerShell:

```powershell
cd task-3\results\exporter
minikube docker-env | Invoke-Expression
docker build -t shipments-exporter:local .
```

CronJob использует:

```yaml
image: shipments-exporter:local
imagePullPolicy: Never
```

Благодаря этому Kubernetes использует образ из локального Docker-демона Minikube.

## 3. Развёртывание Kubernetes-ресурсов

Из директории `task-3/results`:

```bash
kubectl apply -f k8s/
```

Дождаться PostgreSQL:

```bash
kubectl -n shipments-batch get pods
kubectl -n shipments-batch rollout status deployment/postgres
```

## 4. Проверка CronJob и объектов кластера

```bash
kubectl -n shipments-batch get pods
kubectl -n shipments-batch get cronjob
kubectl -n shipments-batch get jobs
kubectl -n shipments-batch get pvc
```

Расписание CronJob:

```yaml
schedule: "0 20 * * *"
timeZone: "Europe/Moscow"
```

Если версия Kubernetes не поддерживает `spec.timeZone` для CronJob, удалите эту строку из `k8s/cronjob.yaml` и примените манифесты повторно. В этом случае расписание будет использовать часовой пояс, настроенный для управляющей плоскости Kubernetes.

## 5. Ручной запуск экспорта

Для демонстрации и скриншотов создать разовый Job из CronJob:

```bash
kubectl -n shipments-batch create job --from=cronjob/shipments-export-cronjob shipments-export-manual
```

Наблюдать за выполнением Job:

```bash
kubectl -n shipments-batch get jobs
kubectl -n shipments-batch get pods
```

## 6. Просмотр логов exporter

Найти pod exporter:

```bash
kubectl -n shipments-batch get pods -l job-name=shipments-export-manual
```

Посмотреть логи:

```bash
kubectl -n shipments-batch logs job/shipments-export-manual
```

Ожидаемые сообщения в логах:

- старт экспорта;
- хост, порт, имя базы данных, пользователь и директория экспорта без пароля;
- количество экспортированных строк;
- путь к созданному CSV;
- успешное завершение.

При ошибке exporter пишет ошибку и стек вызовов в лог, затем завершается с кодом `1`.

## 7. Проверка CSV-файла в PVC

Создать временный pod, который монтирует тот же PVC:

```bash
kubectl -n shipments-batch apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: exports-checker
spec:
  restartPolicy: Never
  containers:
    - name: checker
      image: busybox:1.36
      command: ["sleep", "3600"]
      volumeMounts:
        - name: exports
          mountPath: /exports
  volumes:
    - name: exports
      persistentVolumeClaim:
        claimName: exports-pvc
EOF
```

Дождаться pod для проверки и проверить созданные файлы:

```bash
kubectl -n shipments-batch wait --for=condition=Ready pod/exports-checker --timeout=60s
kubectl -n shipments-batch exec exports-checker -- ls -lah /exports
kubectl -n shipments-batch exec exports-checker -- sh -c "head -n 10 /exports/shipments_*.csv"
```

Удалить pod для проверки:

```bash
kubectl -n shipments-batch delete pod exports-checker
```

## 8. Очистка

```bash
kubectl delete namespace shipments-batch
```

Чтобы отключить текущую командную сессию от Docker-демона Minikube:

Linux/macOS/WSL:

```bash
eval $(minikube docker-env -u)
```

PowerShell:

```powershell
minikube docker-env -u | Invoke-Expression
```

## Скриншоты для сдачи

Сохранить скриншоты в `task-3/results/screenshots/`:

1. `minikube_status.png` - вывод `minikube status`, где видно, что кластер запущен.
2. `docker_build.png` - успешный `docker build -t shipments-exporter:local .`.
3. `kubectl_apply.png` - успешный `kubectl apply -f k8s/`.
4. `postgres_running.png` - PostgreSQL pod находится в рабочем состоянии.
5. `cronjob.png` - `kubectl get cronjob` с расписанием `0 20 * * *`.
6. `manual_job_success.png` - ручной Job создан из CronJob и успешно завершён.
7. `exporter_logs.png` - логи exporter с количеством строк и путём к CSV.
8. `csv_in_pvc.png` - созданный `shipments_YYYYMMDD_HHMMSS.csv` виден в `/exports`.
