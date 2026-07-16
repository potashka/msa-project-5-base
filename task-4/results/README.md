# Задача 4. ETL-архитектура Spring Batch для TradeWare

В этой папке находятся архитектурные материалы задачи 4. Код Spring Boot/Spring Batch приложения здесь не реализуется: результат задания состоит из ADR, C4-диаграммы и сравнения альтернатив.

## Файлы результата

- [ADR-Spring-Batch-TradeWare.md](ADR-Spring-Batch-TradeWare.md) - ADR по выделению CSV ETL в отдельный сервис обработки Spring Batch.
- [c4-spring-batch-to-be.puml](c4-spring-batch-to-be.puml) - C4 Container диаграмма целевой архитектуры.
- [alternatives.md](alternatives.md) - сравнение Apache Airflow, K8s CronJob, Apache Spark, Google Dataflow / Apache Beam, Kafka Streams и Spring Batch.
- [README.md](README.md) - состав результата и инструкция по экспорту диаграммы.

## Как экспортировать C4-диаграмму в PNG

### Вариант 1: PlantUML CLI

Установить Java и PlantUML, затем выполнить из `task-4/results`:

```bash
plantuml -tpng c4-spring-batch-to-be.puml
```

Результатом будет файл:

```text
c4-spring-batch-to-be.png
```

Диаграмма использует подключаемый файл C4-PlantUML из GitHub:

```plantuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
```

Если в окружении PlantUML нет доступа в интернет, скачайте библиотеку C4-PlantUML локально и замените URL в `!include` на локальный путь.

### Вариант 2: Docker-образ PlantUML

Из директории `task-4/results`:

```bash
docker run --rm -v "$PWD:/work" plantuml/plantuml -tpng /work/c4-spring-batch-to-be.puml
```

Пример для PowerShell:

```powershell
docker run --rm -v "${PWD}:/work" plantuml/plantuml -tpng /work/c4-spring-batch-to-be.puml
```

### Вариант 3: Draw.io / diagrams.net

Draw.io не во всех окружениях рендерит PlantUML-текст как нативную диаграмму. Используйте один из подходов:

1. Отрендерить `c4-spring-batch-to-be.puml` в PNG через PlantUML.
2. Открыть diagrams.net.
3. Перетащить PNG на холст или использовать `File -> Import`.
4. Экспортировать итоговую диаграмму через `File -> Export as -> PNG`.

Если в diagrams.net доступен PlantUML-плагин, вставьте содержимое `c4-spring-batch-to-be.puml` в окно импорта/плагина PlantUML и отрендерите диаграмму напрямую.

## Скриншоты для сдачи

Рекомендуемые скриншоты:

1. `adr_overview.png` - ADR с выбранным решением Spring Batch.
2. `c4_spring_batch_to_be.png` - отрендеренная C4 Container диаграмма.
3. `alternatives_table.png` - таблица сравнения альтернатив.
4. `risks_section.png` - раздел ADR с операционными и миграционными рисками.
