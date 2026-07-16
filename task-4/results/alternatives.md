# Альтернативы для ETL TradeWare

## Контекст решения

TradeWare нужно вынести тяжёлую обработку CSV из Java/WildFly-монолита. Ближайшая цель - надёжный ETL для складских отчётов:

- около 400 000 строк в день;
- рост нагрузки в 2-3 раза в пиковые дни;
- 100-150 параллельных загрузок в пиковые часы;
- среднее время обработки отчёта на 2 000 строк - до 30 секунд;
- Java-команда, PostgreSQL и GCS уже используются;
- нужен путь миграции к микросервисам.

Spring Batch выбран для ближайшего этапа, потому что решает текущую проблему с минимальным технологическим скачком.

## Сравнение

| Альтернатива | Сильные стороны | Слабые стороны для этого сценария | Соответствие задаче |
|---|---|---|---|
| Apache Airflow | Сильная оркестрация, DAG UI, retries, расписания, хорошая видимость многошаговых пайплайнов. | Airflow - оркестратор, а не движок построчной обработки. Для chunk processing, построчной валидации, skip/retry и JDBC upsert всё равно нужен отдельный worker/service. Добавляет отдельную платформу в эксплуатацию. | Полезен позже, если TradeWare потребуются многочисленные зависимые data pipelines, расписания и межсистемная оркестрация. Не лучший первый шаг для выноса обработки. |
| Kubernetes CronJob | Простые cloud-native scheduled jobs, лёгкое развёртывание в Kubernetes, низкий overhead. | Нагрузка состоит из пользовательских загрузок множества файлов, а не только из ежедневной задачи по расписанию. У CronJob ограниченный lifecycle UX и нет встроенных chunk restartability, skip policy или JobRepository. | Хорош для простых регулярных импортов/экспортов. Слишком примитивен для интерактивной обработки CSV при пиковой конкуренции. |
| Apache Spark | Распределённая обработка, сильная работа с большими наборами данных, partitioning, масштабируемый compute. | Операционно тяжелее. Нужен Spark cluster/operator или managed service. Для 400k-1.2M строк в день и отчётов по 2k строк Spark, скорее всего, избыточен. Java-команда получит более сложную реализацию и эксплуатацию. | Хорош, если данные вырастут до десятков/сотен миллионов строк или трансформации станут аналитическими и распределёнными. |
| Google Dataflow / Apache Beam | Managed scaling, сильная batch/stream-модель, GCP-native подход, хорош для крупных data pipelines. | Требует модели программирования Beam и более сильной привязки к облаку. Дороже по learning curve и операционной модели, чем Spring Batch. Интеграция со статусным UX монолита и бизнес-валидацией строк требует дополнительного дизайна. | Сильная будущая опция для cloud-native миграции data platform. Не самый малый ближайший шаг. |
| Kafka Streams | Отличен для event streams, stateful stream processing и непрерывных обновлений. | Текущий источник - загруженные CSV-файлы в GCS. Kafka Streams неестественен для file-based import с chunk restartability и отчётами по пропущенным строкам. Потребуется превращать строки файла в события и проектировать topics, ordering и replay. | Полезен позже, если TradeWare перейдёт к event-driven обновлениям inventory/nomenclature. Не идеален для выноса CSV ETL из монолита. |
| Spring Batch | Создан для batch jobs, chunk-oriented processing, retry/skip/restartability, JobRepository, Java/JDBC integration, привычен Java-командам. | Добавляет новый сервис и metadata repository. Требует аккуратного проектирования idempotency, контроля parallelism и нагрузки на БД. Не является распределённым big-data engine. | Лучший ближайший выбор для выноса CSV processing из Java-монолита с сохранением близости к текущему стеку. |

## Почему Spring Batch выбран для ближайшего этапа

Spring Batch напрямую закрывает текущий failure mode: долгая построчная обработка блокирует online-монолит. Он переносит нагрузку в отдельный processing service, сохраняя привычную интеграцию с Java, PostgreSQL и GCS.

Ключевые причины:

- chunk-oriented processing снижает транзакционный overhead и не требует загружать целые файлы в память;
- JobRepository даёт статус job/step, restartability и историю выполнения;
- retry, skip и backoff являются встроенными паттернами;
- idempotent upsert можно реализовать рядом с существующей доменной логикой;
- Java-команда может проще переиспользовать существующий код валидации и enrichment, чем при Spark/Dataflow;
- монолит может постепенно превратиться в тонкий upload/status facade без полного переписывания;
- Kubernetes scaling можно добавить постепенно через дополнительные реплики сервиса, partitioning и лимиты конкуренции.

## Ограничения Spring Batch

Spring Batch не является универсальной data platform. Основные ограничения для TradeWare:

- он не отменяет необходимость проектировать concurrency control;
- PostgreSQL всё ещё может стать bottleneck, если слишком много jobs одновременно пишут данные;
- partitioning и multithreaded steps требуют thread-safe readers, processors и writers;
- JobRepository нужно мониторить и обслуживать;
- очень большие распределённые нагрузки со временем могут потребовать Spark или Dataflow;
- асинхронный UX нужно явно спроектировать в монолите и frontend;
- нужна операционная зрелость: dashboards, alerts, обработка failed jobs, процедуры restart и runbooks.

## Рекомендуемая эволюция

1. Вынести CSV processing в Spring Batch Processing Service.
2. Добавить JobRepository, status API и async upload UX.
3. Добавить metrics, logs, alerting и operational runbooks.
4. Настроить chunk size, индексы БД, batch writes и connection pools.
5. Добавить контролируемый parallelism и partitioning после baseline-измерений.
6. Вернуться к Airflow/Dataflow/Spark только если пайплайны станут межсистемными, жёстко расписанными или действительно распределёнными на большем масштабе.
