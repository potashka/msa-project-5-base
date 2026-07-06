# Implementation plan

## 1. Prepare SQL query

- Define the exact output columns for B2B price lists.
- Prepare SQL JOIN across `products`, `categories`, `clients` and `client_prices`.
- Validate filtering rules for active products, active clients, currencies and special client prices.
- Check indexes for join keys and filtering columns.

## 2. Create exporter application

- Build a small stateless `price-list-exporter` application.
- Read configuration from environment variables.
- Connect to PostgreSQL with a read-only user.
- Execute the prepared SQL query.
- Stream result rows to CSV or XLS without loading unnecessary data into memory.
- Exit with code `0` on success and non-zero code on failure.

## 3. Create Dockerfile

- Package the exporter into a minimal Docker image.
- Add health-neutral startup behavior: the container should run once and exit.
- Pin runtime dependencies.
- Publish the image to the project container registry.

## 4. Create ConfigMap and Secret

- Put non-sensitive settings into `ConfigMap`:
  - database host;
  - database port;
  - database name;
  - output format;
  - storage bucket/path;
  - timezone, if required.
- Put sensitive values into `Secret`:
  - database username;
  - database password;
  - storage credentials, if IAM/Workload Identity is not used.

## 5. Create Kubernetes CronJob

- Define CronJob with schedule:

```yaml
schedule: "0 6 * * *"
timeZone: "Europe/Moscow"
```

- Use the `price-list-exporter` image.
- Inject `ConfigMap` and `Secret` as environment variables.
- Mount PVC only for local POC if object storage is not used.

## 6. Configure resources and reliability

- Set CPU/memory requests and limits.
- Configure `concurrencyPolicy: Forbid`.
- Configure `backoffLimit` to limit retries after failures.
- Configure `restartPolicy: Never` or `OnFailure` according to the final retry strategy.
- Configure `successfulJobsHistoryLimit` and `failedJobsHistoryLimit`.
- Add `activeDeadlineSeconds` to prevent a stuck export from running indefinitely.

## 7. Configure CSV/XLS storage

- Production option: save generated files to S3/GCS.
- Local POC option: save generated files to PVC.
- Use deterministic file naming, for example:

```text
price-lists/yyyy-mm-dd/client-<client_id>.csv
```

- Define retention policy for old files.

## 8. Configure logs and metrics

- Write structured JSON logs to stdout.
- Log start time, finish time, duration, number of clients, number of rows, output location and final status.
- Collect Kubernetes Job/Pod metrics with Prometheus.
- Configure alerts for:
  - failed job;
  - no successful run after 06:00;
  - execution duration above expected threshold;
  - storage write failure.

## 9. Verify locally in Minikube

- Build and load the Docker image into Minikube.
- Deploy PostgreSQL test data or connect to a test database.
- Apply `ConfigMap`, `Secret`, PVC and CronJob manifests.
- Trigger the Job manually from the CronJob for validation.
- Check generated CSV/XLS file.
- Check logs and Job status.

## 10. Move to cloud Kubernetes

- Publish image to cloud container registry.
- Replace local PVC with S3/GCS integration.
- Configure cloud IAM/Workload Identity for storage access.
- Deploy manifests through CI/CD or Helm/Kustomize.
- Verify the scheduled 06:00 run in the target timezone.
- Add dashboard and alert rules to production monitoring.
