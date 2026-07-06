# Task 4. Spring Batch ETL architecture for TradeWare

В этой папке находятся архитектурные материалы Task4. Код Spring Boot/Spring Batch приложения здесь не реализуется: результат задания состоит из ADR, C4-диаграммы и сравнения альтернатив.

## Result files

- [ADR-Spring-Batch-TradeWare.md](ADR-Spring-Batch-TradeWare.md) - ADR по выделению CSV ETL в отдельный Spring Batch Processing Service.
- [c4-spring-batch-to-be.puml](c4-spring-batch-to-be.puml) - C4 Container диаграмма целевой архитектуры.
- [alternatives.md](alternatives.md) - сравнение Apache Airflow, K8s CronJob, Apache Spark, Google Dataflow / Apache Beam, Kafka Streams и Spring Batch.
- [README.md](README.md) - состав результата и инструкция по экспорту диаграммы.

## How to export C4 diagram to PNG

### Option 1: PlantUML CLI

Install Java and PlantUML, then run from `task-4/results`:

```bash
plantuml -tpng c4-spring-batch-to-be.puml
```

The result will be:

```text
c4-spring-batch-to-be.png
```

The diagram uses C4-PlantUML includes from GitHub:

```plantuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
```

If your PlantUML environment has no internet access, download the C4-PlantUML library locally and replace the `!include` URL with a local path.

### Option 2: PlantUML Docker image

From `task-4/results`:

```bash
docker run --rm -v "$PWD:/work" plantuml/plantuml -tpng /work/c4-spring-batch-to-be.puml
```

PowerShell example:

```powershell
docker run --rm -v "${PWD}:/work" plantuml/plantuml -tpng /work/c4-spring-batch-to-be.puml
```

### Option 3: Draw.io / diagrams.net

Draw.io does not render PlantUML text as a native diagram in every setup. Use one of these approaches:

1. Render `c4-spring-batch-to-be.puml` to PNG through PlantUML.
2. Open diagrams.net.
3. Drag the PNG into the canvas or use `File -> Import`.
4. Export the final diagram through `File -> Export as -> PNG`.

If a PlantUML plugin is available in your diagrams.net environment, paste the contents of `c4-spring-batch-to-be.puml` into the PlantUML plugin/import dialog and render it directly.

## Screenshots for submission

Recommended screenshots:

1. `adr_overview.png` - ADR with the selected Spring Batch decision.
2. `c4_spring_batch_to_be.png` - rendered C4 Container diagram.
3. `alternatives_table.png` - alternatives comparison table.
4. `risks_section.png` - ADR risk section with operational and migration risks.
