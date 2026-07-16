# ADR: Spring Batch ETL for TradeWare warehouse reports

## Название задачи

Архитектурное решение ETL для обработки CSV-отчетов TradeWare с использованием Spring Batch.

## Автор

Solution Architecture Team / TradeWare project.

## Дата

2026-07-07

## Функциональные требования

- Пользователь склада загружает CSV-отчет через ERP-интерфейс.
- Система должна принимать файл, сохранять его в GCS и запускать асинхронную обработку.
- Обработка должна валидировать CSV, построчно читать данные, обогащать их справочниками и обновлять БД номенклатуры.
- Монолит должен показывать пользователю статус обработки: accepted, processing, completed, completed with warnings, failed.
- Должна быть возможность повторного запуска failed job без дублирования уже обработанных данных.
- Должна быть история job/step execution, ошибок, пропущенных строк и итоговых счетчиков.
- Нужно поддержать 100-150 параллельных загрузок в пиковые часы.
- Среднее время обработки отчета на 2 000 строк должно быть до 30 секунд.

## Нефункциональные требования

- Суточный объем: около 400 000 строк, в пиковые дни рост в 2-3 раза.
- Обработка загрузок не должна тормозить ERP-интерфейс и основной Java/WildFly монолит.
- Решение должно быть совместимо с текущим стеком: Java, PostgreSQL, GCS.
- Нужна подготовка к микросервисной архитектуре через выделение batch processing в отдельный сервис.
- Нужны централизованные логи, метрики, алерты и наблюдаемость по job/step.
- Нужна управляемая параллельность, чтобы batch jobs не перегружали PostgreSQL.
- Нужны retry, skip policy, backoff и идемпотентность.
- Решение должно позволять горизонтальное масштабирование batch workers.

## Решение

Выделить обработку CSV-отчетов из WildFly-монолита в отдельный **Spring Batch Processing Service**.

### Текущие проблемы

Сейчас Java-монолит делает слишком много в одном online request flow:

- принимает CSV через ERP-интерфейс;
- валидирует файл;
- сохраняет файл в GCS;
- построчно обрабатывает данные;
- обогащает строки справочниками;
- пишет результат в PostgreSQL;
- удерживает ресурсы приложения во время тяжелой обработки.

Из-за этого при пиковых загрузках:

- worker threads монолита заняты долгими операциями;
- соединения к PostgreSQL удерживаются дольше, чем нужно online-сценариям;
- ERP-интерфейс начинает тормозить;
- пользовательский request lifecycle смешан с batch lifecycle;
- сложно изолировать ошибки обработки файла от ошибок пользовательского интерфейса;
- нет полноценной модели restartability, skip/retry и статусов step-level обработки.

Построчная онлайн-обработка перегружает монолит, потому что batch workload имеет другую природу: он длительный, объемный, чувствительный к backpressure и требует отдельного контроля параллелизма. Online ERP-запросы должны быть короткими и предсказуемыми, а не конкурировать с тяжелым импортом CSV за CPU, heap, JDBC pool и transaction resources.

### Целевая архитектура

Монолит остается точкой входа для загрузки файла и UX-статуса, но перестает выполнять тяжелую обработку.

Новый поток:

1. Warehouse Employee загружает CSV через Angular Frontend.
2. Angular Frontend отправляет файл в Java/WildFly Monolith.
3. Монолит выполняет первичную проверку: размер, формат имени, базовые metadata.
4. Монолит сохраняет исходный CSV в GCS File Storage.
5. Монолит создает batch job request для Spring Batch Processing Service, передавая `file_uri`, `upload_id`, `tenant/client context` и параметры обработки.
6. Spring Batch Processing Service создает запись в JobRepository и запускает job.
7. Reader читает CSV из GCS.
8. Processor валидирует строки и обогащает данные справочниками из PostgreSQL Reference DB.
9. Writer записывает нормализованные данные в PostgreSQL Nomenclature DB.
10. JobRepository хранит статусы job/step, счетчики read/process/write/skip, параметры запуска и ошибки.
11. Monitoring/Logging собирает метрики, логи и алерты.
12. Монолит показывает пользователю статус, читая его через API batch service или из batch metadata/status projection.

### Spring Batch Processing Service

Сервис реализуется как отдельное Java/Spring Boot приложение со Spring Batch. Он может запускаться в Kubernetes как Deployment с несколькими репликами или как управляемые batch workers. На ближайшем этапе это естественный эволюционный шаг для Java-команды: сохраняется привычный язык, Spring ecosystem, JDBC/PostgreSQL, транзакционная модель и понятная эксплуатационная модель.

Ключевые элементы:

- `Job`: обработка одного загруженного CSV-файла.
- `JobParameters`: `upload_id`, `file_uri`, дата загрузки, пользователь/организация, checksum.
- `ItemReader`: streaming-чтение CSV из GCS.
- `ItemProcessor`: валидация строки, нормализация, обогащение справочниками.
- `ItemWriter`: batch insert/update/upsert в PostgreSQL Nomenclature DB.
- `JobRepository`: хранение metadata job/step execution.
- `JobExplorer`/`JobOperator`: просмотр статусов, restart/stop job.

### GCS как источник файлов

GCS остается durable storage для исходных CSV:

- монолит быстро сохраняет файл и освобождает online request;
- batch service читает файл асинхронно;
- исходный файл можно переобработать при ошибке;
- можно хранить audit trail и checksum;
- можно настроить lifecycle policy для старых файлов.

### PostgreSQL как источник справочников и целевая БД

PostgreSQL Reference DB используется для справочников: товары, категории, склады, единицы измерения, правила нормализации. PostgreSQL Nomenclature DB является целевой БД для обновления номенклатуры.

Для защиты PostgreSQL нужно:

- использовать отдельные connection pools для batch service;
- ограничить параллельность job/partition;
- применять batch writes;
- кешировать редко меняющиеся справочники внутри step/job;
- индексировать lookup и target keys;
- использовать idempotent upsert по бизнес-ключам.

### JobRepository

JobRepository хранит состояние Spring Batch:

- параметры запуска job;
- статус job и step;
- время старта и завершения;
- read/write/skip counters;
- exceptions и exit status;
- данные для restartability.

Для production JobRepository лучше выделить в отдельную схему или отдельную PostgreSQL database, чтобы metadata batch-процессов не смешивались с бизнес-таблицами.

### Chunk-oriented processing

Spring Batch должен использовать chunk-oriented processing:

```text
read N rows -> process N rows -> write N rows -> commit transaction
```

Рекомендуемый стартовый chunk size: 500-2 000 строк. Точное значение подбирается нагрузочным тестированием.

Плюсы:

- меньше транзакций, чем при построчной записи;
- контролируемое потребление памяти;
- понятные retry/skip границы;
- restart с последнего сохраненного состояния step;
- batch insert/update снижает нагрузку на PostgreSQL.

### Retry, skip, backoff, idempotency

Для надежности обработки:

- retry применять для временных ошибок: network timeout, transient DB error, temporary GCS read issue;
- backoff использовать, чтобы не добивать зависимый сервис при деградации;
- skip применять для data quality ошибок конкретных строк, если бизнес допускает partial success;
- лимит skip должен быть настроен явно, например процент или абсолютное число строк;
- bad rows сохранять в error report в GCS или отдельную таблицу ошибок;
- idempotency строить на `upload_id`, checksum файла и бизнес-ключах строк;
- запись в целевую БД выполнять через deterministic upsert, чтобы повторный запуск не создавал дубликаты.

### Partitioning and multithreaded step

Для достижения 100-150 параллельных загрузок и обработки пиков в 2-3 раза нужны контролируемые модели масштабирования:

- multithreaded step для ускорения обработки одного файла, если reader/processor/writer потокобезопасны;
- partitioning по диапазонам строк, batch segments или file split;
- ограничение максимального числа активных job;
- горизонтальное масштабирование batch service replicas;
- очередь job requests, если пик превышает безопасную параллельность PostgreSQL.

Важно: параллельность должна быть ограничена не только CPU сервиса, но и возможностями PostgreSQL, GCS bandwidth и допустимой задержкой online-сценариев.

### Роль монолита после изменений

Java/WildFly Monolith остается в системе, но его ответственность сужается:

- принять файл от ERP UI;
- выполнить быстрые synchronous checks;
- сохранить файл в GCS;
- создать batch job request;
- вернуть пользователю `upload_id` и статус `accepted`;
- показывать статус обработки;
- отображать error report после завершения.

Монолит больше не выполняет тяжелую построчную обработку в online request. UX меняется с синхронного ожидания результата на асинхронную модель статуса обработки.

### Почему Spring Batch подходит Java-команде и текущему стеку

Spring Batch выбран для ближайшего этапа, потому что:

- команда уже работает в Java ecosystem;
- решение хорошо ложится рядом с текущим Java/WildFly монолитом;
- Spring Batch специально создан для надежной batch-обработки;
- есть готовые паттерны chunk processing, retry, skip, restartability и JobRepository;
- легко интегрируется с PostgreSQL через JDBC;
- GCS можно подключить через Google Cloud SDK или Spring Cloud GCP;
- проще внедрить постепенно, чем сразу переносить ETL на Spark/Dataflow;
- это хороший шаг к микросервисной декомпозиции без резкого изменения технологического стека.

## Альтернативы

- Оставить обработку в монолите и оптимизировать JDBC/threads. Не решает архитектурное смешение online и batch workloads.
- Apache Airflow. Хорош как orchestration layer, но для построчной Java-ориентированной обработки CSV с restartability на уровне chunk нужен отдельный processing engine.
- Kubernetes CronJob. Подходит для регулярных задач, но хуже для 100-150 пользовательских асинхронных загрузок в течение пикового окна.
- Apache Spark. Силен на больших распределенных данных, но избыточен для 400 000-1 200 000 строк/сутки и усложняет эксплуатацию.
- Google Dataflow / Apache Beam. Хорош для managed data pipelines, но требует другой модели разработки и облачной привязки.
- Kafka Streams. Подходит для event streaming, но CSV file import с retry/skip/restartability проще реализовать Spring Batch.

Подробное сравнение вынесено в [alternatives.md](alternatives.md).

## Недостатки, ограничения, риски

- **Усложнение эксплуатации.** Появляется отдельный batch service, deployment, scaling policy, connection pool и release lifecycle.
- **Необходимость проектировать идемпотентность.** Повторный запуск job, retry chunk и partial failure не должны создавать дубликаты или портить номенклатуру.
- **Контроль параллельных job.** 100-150 параллельных загрузок требуют лимитов, очереди или throttling, иначе можно перегрузить БД.
- **Нагрузка на PostgreSQL.** Batch reads/writes и lookup справочников могут конкурировать с online-трафиком. Нужны индексы, batch writes, pool limits и мониторинг.
- **Необходимость отдельного мониторинга job.** Нужны метрики job duration, failed jobs, skipped rows, queue depth, DB latency, chunk retries, GCS read errors.
- **Миграция от синхронного UX к асинхронному статусу обработки.** Пользователь больше не должен ждать завершения импорта в одном HTTP-запросе. Нужно изменить UI и ожидания бизнеса.
- **Сложность skip policy.** Нужно согласовать, какие ошибки строк можно пропускать, а какие должны валить весь файл.
- **Согласованность справочников.** При долгой обработке справочники могут измениться. Нужна стратегия snapshot/cache/versioning.
- **Ограничения Spring Batch для очень больших объемов.** Если объемы вырастут на порядки или появятся сложные распределенные трансформации, может потребоваться Spark/Dataflow.
