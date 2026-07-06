# Task 2. To Be batch architecture for price-list export

В этой папке находятся результаты дизайн-задания Task 2 для TradeWare. Полноценный код exporter-приложения здесь не реализуется: реализация относится к Task 3.

## Result files

- [comparison-table.md](comparison-table.md) - сравнение Spring Batch, Apache Airflow, Kubernetes Job/CronJob и Apache Spark.
- [solution.md](solution.md) - описание выбранного решения на базе Kubernetes CronJob `price-list-exporter`.
- [c4-to-be.puml](c4-to-be.puml) - C4 Context/Container диаграмма To Be в формате PlantUML.
- [implementation-plan.md](implementation-plan.md) - верхнеуровневый план внедрения решения.
- [README.md](README.md) - краткое описание состава результатов и скриншотов для сдачи.

## Screenshots to attach

Для сдачи рекомендуется приложить скриншоты в отдельную папку `screenshots/`:

1. `comparison_table.png` - открытая таблица сравнения из `comparison-table.md`.
2. `c4_to_be_diagram.png` - отрендеренная C4 To Be диаграмма из `c4-to-be.puml`.
3. `solution_overview.png` - фрагмент `solution.md` с выбранной архитектурой.
4. `implementation_plan.png` - фрагмент `implementation-plan.md` с планом внедрения.

Если преподаватель принимает исходные Markdown/PlantUML-файлы без скриншотов, достаточно приложить содержимое этой папки.
