# Task 3. Distributed Scheduling with Kubernetes CronJob

Результат Task3: локальный Minikube POC для ежедневной выгрузки аналитических данных из PostgreSQL в CSV через Kubernetes CronJob.

CronJob запускает контейнер `shipments-exporter:local` каждый день в 20:00 по московскому времени, exporter читает таблицу `shipments` из PostgreSQL и сохраняет CSV-файл в PVC `/exports`.

## Structure

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

## Requirements

- Docker Desktop or Docker Engine
- Minikube
- kubectl

No external image registry is used. The Docker image is built directly inside the Minikube Docker daemon.

## 1. Start Minikube

```bash
minikube start
```

Check cluster status:

```bash
minikube status
kubectl cluster-info
```

## 2. Build Docker image in Minikube

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

The CronJob uses:

```yaml
image: shipments-exporter:local
imagePullPolicy: Never
```

This makes Kubernetes use the image from Minikube's local Docker daemon.

## 3. Deploy Kubernetes resources

From `task-3/results`:

```bash
kubectl apply -f k8s/
```

Wait for PostgreSQL:

```bash
kubectl -n shipments-batch get pods
kubectl -n shipments-batch rollout status deployment/postgres
```

## 4. Check CronJob and cluster objects

```bash
kubectl -n shipments-batch get pods
kubectl -n shipments-batch get cronjob
kubectl -n shipments-batch get jobs
kubectl -n shipments-batch get pvc
```

The CronJob schedule is:

```yaml
schedule: "0 20 * * *"
timeZone: "Europe/Moscow"
```

If your Kubernetes version does not support `spec.timeZone` for CronJob, remove this line from `k8s/cronjob.yaml` and apply the manifests again. In that case the schedule will use the timezone configured for the Kubernetes control plane.

## 5. Run export manually

For demo and screenshots, create a one-time Job from the CronJob:

```bash
kubectl -n shipments-batch create job --from=cronjob/shipments-export-cronjob shipments-export-manual
```

Watch job execution:

```bash
kubectl -n shipments-batch get jobs
kubectl -n shipments-batch get pods
```

## 6. View exporter logs

Find the exporter pod:

```bash
kubectl -n shipments-batch get pods -l job-name=shipments-export-manual
```

View logs:

```bash
kubectl -n shipments-batch logs job/shipments-export-manual
```

Expected log messages include:

- export start;
- database host, port, db name, user and export directory without password;
- number of exported rows;
- generated CSV path;
- successful completion.

On failure, the exporter logs the error and stacktrace, then exits with code `1`.

## 7. Check CSV file in PVC

Create a temporary pod that mounts the same PVC:

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

Wait for the checker pod and inspect generated files:

```bash
kubectl -n shipments-batch wait --for=condition=Ready pod/exports-checker --timeout=60s
kubectl -n shipments-batch exec exports-checker -- ls -lah /exports
kubectl -n shipments-batch exec exports-checker -- sh -c "head -n 10 /exports/shipments_*.csv"
```

Cleanup checker pod:

```bash
kubectl -n shipments-batch delete pod exports-checker
```

## 8. Cleanup

```bash
kubectl delete namespace shipments-batch
```

To disconnect the current shell from Minikube Docker daemon:

Linux/macOS/WSL:

```bash
eval $(minikube docker-env -u)
```

PowerShell:

```powershell
minikube docker-env -u | Invoke-Expression
```

## Screenshots for submission

Put screenshots into `task-3/results/screenshots/`:

1. `minikube_status.png` - `minikube status` and cluster is running.
2. `docker_build.png` - successful `docker build -t shipments-exporter:local .`.
3. `kubectl_apply.png` - successful `kubectl apply -f k8s/`.
4. `postgres_running.png` - PostgreSQL pod is running.
5. `cronjob.png` - `kubectl get cronjob` with schedule `0 20 * * *`.
6. `manual_job_success.png` - manual job created from CronJob and completed.
7. `exporter_logs.png` - exporter logs with row count and CSV path.
8. `csv_in_pvc.png` - generated `shipments_YYYYMMDD_HHMMSS.csv` visible in `/exports`.
