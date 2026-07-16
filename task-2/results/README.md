# Задача 2. Целевая архитектура пакетной обработки для экспорта прайс-листов

В этой папке находятся результаты дизайн-задания задачи 2 для TradeWare. Полноценный код приложения exporter здесь не реализуется: реализация относится к задаче 3.

## Файлы результата

- [comparison-table.md](comparison-table.md) - сравнение Spring Batch, Apache Airflow, Kubernetes Job/CronJob и Apache Spark.
- [solution.md](solution.md) - описание выбранного решения на базе Kubernetes CronJob `price-list-exporter`.
- [c4-to-be.puml](c4-to-be.puml) - целевая C4 Context/Container диаграмма в формате PlantUML.
- [implementation-plan.md](implementation-plan.md) - верхнеуровневый план внедрения решения.
- [README.md](README.md) - краткое описание состава результатов и скриншотов для сдачи.

## Скриншоты для приложения к сдаче

Для сдачи рекомендуется приложить скриншоты в отдельную папку `screenshots/`:

1. `comparison_table.png` - открытая таблица сравнения из `comparison-table.md`.
2. `c4_to_be_diagram.png` - отрендеренная целевая C4-диаграмма из `c4-to-be.puml`.
3. `solution_overview.png` - фрагмент `solution.md` с выбранной архитектурой.
4. `implementation_plan.png` - фрагмент `implementation-plan.md` с планом внедрения.

Если преподаватель принимает исходные Markdown/PlantUML-файлы без скриншотов, достаточно приложить содержимое этой папки.
