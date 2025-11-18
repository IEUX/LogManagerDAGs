from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from confluent_kafka import Consumer
import re
import os
import pandas as pd
import clickhouse_connect

# [SENT] 2025-10-27 12:52:42 [ERROR] (user-service) Token expired, re-authenticating

client = clickhouse_connect.get_client(
    host="logsmanager-clickhouse-1",  # or your ClickHouse server
    port=8123,  # default HTTP port
    username="root",
    password="root",
)


def consume_kafka_messages(**context):
    # CONF

    pattern = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([A-Z]+)\] \(([^)]+)\) (.+)$"
    conf = {
        "bootstrap.servers": "kafka1:9092",
        "group.id": "airflow-consumer-group",
        "auto.offset.reset": "earliest",
    }
    consumer = Consumer(conf)
    services = os.getenv("AVAILABLE_SERVICES").split(" ")
    consumer.subscribe(services)
    messages = []

    # EXTRACT

    for _ in range(40):
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        match = re.match(pattern, msg.value().decode("utf-8"))
        if match:
            timestamp, level, service, message = match.groups()
            if level != "DEBUG":
                log = {
                    "timestamp": timestamp,
                    "service": msg.topic(),
                    "level": level,
                    "user": service,
                    "log": message,
                }
                messages.append(log)
        else:
            print(f"Format error: {msg.value().decode('utf-8')}")
    consumer.close()

    # TRANSFORM

    df = pd.DataFrame(messages)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    service_groups = df.groupby("service")

    # LOAD

    for service, group in service_groups:
        # Table name based on service
        table_name = f"events_{service.lower()}"

        # Create table if it doesn’t exist
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            timestamp DateTime,
            service String,
            level String,
            user String,
            log String
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (timestamp, level)
        """
        client.command(create_table_query)

        # Insert subset of data
        client.insert_df(table_name, group)

        print(f"✅ Inserted {len(group)} rows into table '{table_name}'")


with DAG(
    dag_id="transformLogsFromKafka",
    start_date=datetime(2025, 10, 27),
    schedule_interval="*/10 * * * *",
    catchup=False,
) as dag:
    consume_task = PythonOperator(
        task_id="consume_kafka_messages", python_callable=consume_kafka_messages
    )
