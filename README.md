# MSA Project 5 - Batch Processing, Scheduling and Observability

Проект посвящён архитектурным и практическим решениям для batch processing, distributed scheduling и observability в микросервисной среде.

В рамках работы рассмотрены:

- выбор решений для пакетной обработки данных;
- проектирование scheduled jobs;
- реализация Kubernetes CronJob;
- внедрение Spring Batch в архитектуру TradeWare;
- проектирование observability: мониторинг, логирование и алертинг.

## Структура репозитория

Фактическая структура проекта:

```text
.
+-- task-1/
|   +-- results/
+-- task-2/
|   +-- results/
+-- task-3/
|   +-- results/
+-- task-4/
|   +-- results/
+-- task-5/
|   +-- results/
+-- .gitignore
+-- README.md
```

## Задачи

| Task | Цель | Выбранное решение | Основные артефакты | Где смотреть |
|------|------|-------------------|--------------------|--------------|
| Task1 | Выбор и POC решения для пакетной обработки данных | Apache Airflow | Обоснование выбора, Docker Compose, DAG, чтение PostgreSQL/CSV, ветвление pipeline, retry, email-уведомления | [task-1/results](task-1/results) |
| Task2 | Дизайн модуля генерации B2B price-list | Kubernetes CronJob | Сравнительная таблица Spring Batch / Airflow / K8s Job / Spark, C4 To Be, план имплементации | [task-2/results](task-2/results) |
| Task3 | Реализация Distributed Scheduling через Kubernetes CronJob | K8s CronJob + Python exporter + Minikube | Python exporter, Dockerfile, Kubernetes YAML, PostgreSQL в Minikube, CronJob на 20:00, экспорт `shipments` в CSV | [task-3/results](task-3/results) |
| Task4 | Архитектурное решение ETL для TradeWare | Spring Batch | ADR, C4 To Be, Spring Batch Processing Service, альтернативы и риски | [task-4/results](task-4/results) |
| Task5 | Проектирование мониторинга, логирования и оповещения | Prometheus/Grafana/Alertmanager + ELK/OpenSearch | Observability C4, метрики, структурированные логи, алерты, примеры Prometheus и Fluent Bit конфигов | [task-5/results](task-5/results) |

## Local environment

Проект выполнялся и рассчитан на локальную проверку в окружении:

- Windows 11;
- Docker Desktop;
- WSL2 Ubuntu;
- Minikube;
- kubectl;
- PostgreSQL client;
- Draw.io / PlantUML.

Проверка базовых инструментов:

```bash
docker version
docker compose version
kubectl version --client
minikube version
```

## Установка инструментов в WSL2

Базовые пакеты:

```bash
sudo apt update
sudo apt install -y git curl unzip make jq ca-certificates gnupg postgresql-client
```

Установка `kubectl`:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

Установка Minikube:

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube version
```

Запуск Minikube:

```bash
minikube start --driver=docker --cpus=4 --memory=6144
kubectl get nodes
```

## How to run

Подробные инструкции находятся внутри README соответствующих задач. Корневой README даёт только быстрые точки входа.

### Task1: Apache Airflow POC

```bash
cd task-1/results
docker compose up -d --build
```

Дальше см. [task-1/results/README.md](task-1/results/README.md).

### Task3: Kubernetes CronJob в Minikube

```bash
cd task-3/results
minikube start --driver=docker
eval $(minikube docker-env)
docker build -t shipments-exporter:local ./exporter
kubectl apply -f k8s/
kubectl -n shipments-batch create job --from=cronjob/shipments-export-cronjob shipments-export-manual
kubectl -n shipments-batch logs job/shipments-export-manual
```

Дальше см. [task-3/results/README.md](task-3/results/README.md).

### Task2, Task4, Task5

Это архитектурные задания. Запуск не требуется:

- Task2: [task-2/results](task-2/results);
- Task4: [task-4/results](task-4/results);
- Task5: [task-5/results](task-5/results).

Смотреть Markdown-документы, ADR, таблицы и C4-диаграммы.

## Diagrams

Диаграммы находятся внутри соответствующих директорий `task-*/results`.

В проекте используются:

- `.puml` - PlantUML / C4-PlantUML диаграммы;
- `.md` - архитектурные описания, ADR, таблицы;
- `.png` / `.svg` - экспортированные версии диаграмм, если они добавляются для сдачи.

Для просмотра и экспорта можно использовать:

- Draw.io / diagrams.net;
- PlantUML;
- Markdown preview в IDE или GitHub.

Пример экспорта PlantUML в PNG:

```bash
plantuml -tpng task-4/results/c4-spring-batch-to-be.puml
plantuml -tpng task-5/results/c4-observability-to-be.puml
```

## Submission checklist

- [ ] Все результаты находятся в директориях `task-1/results` ... `task-5/results`.
- [ ] В Task1 приложены DAG/config и скриншоты POC.
- [ ] В Task2 есть таблица сравнения, C4 To Be и план имплементации.
- [ ] В Task3 есть Dockerfile, exporter, k8s YAML и скриншоты Minikube.
- [ ] В Task4 есть ADR и C4-диаграмма Spring Batch.
- [ ] В Task5 есть observability C4, метрики, логи и алерты.
- [ ] Все README обновлены.
- [ ] Pull Request содержит все изменения.
- [ ] Репозиторий публичный.

## Git commands

```bash
git status
git add .
git commit -m "Add project documentation and task results"
git push origin solution
```
