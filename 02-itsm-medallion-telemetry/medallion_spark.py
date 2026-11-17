#!/usr/bin/env python3
"""
================================================================================
METADATA HEADER: ENGINEERING & GOVERNANCE ALIGNMENT
Artifact:        02-itsm-medallion-telemetry/medallion_spark.py
Domain Scope:    site-mfg-01 | enclave-cui-prod | org-enterprise-it
NIST SP 800-171: 3.3.1 (System Auditing), 3.4.1 (Baseline Configuration / CMDB),
                 3.12.3 (Continuous Security & Operational Monitoring)
ITIL 4 / PMI:    ITIL 4 Incident & Service Request Mgmt, Service Config Mgmt |
                 PMI Empirical Queue Bottleneck & SLA Breach Governance
================================================================================

PySpark + Delta Lake Medallion implementation for Databricks / Enterprise Spark
clusters. Transforms raw 90-day ServiceNow & CMDB extracts into Bronze, Silver,
and Gold Delta tables.
"""

from __future__ import annotations

from typing import Any


def build_pyspark_medallion_pipeline(
    spark: Any,
    raw_base_path: str,
    delta_base_path: str,
) -> dict[str, Any]:
    """
    Executes the PySpark + Delta Lake Bronze -> Silver -> Gold transformations
    when running inside a Databricks or Apache Spark runtime.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window

    # 1. BRONZE LAYER: Raw schema-enforced ingestion with audit metadata
    bronze_inc = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(f"{raw_base_path}/servicenow_incidents_90d.csv")
        .withColumn("_ingested_at_utc", F.current_timestamp())
        .withColumn("_source_system", F.lit("ServiceNow-TableAPI-90d"))
    )
    bronze_cmdb = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(f"{raw_base_path}/cmdb_ci_inventory.csv")
        .withColumn("_ingested_at_utc", F.current_timestamp())
    )

    bronze_inc.write.format("delta").mode("overwrite").save(f"{delta_base_path}/bronze/incidents")
    bronze_cmdb.write.format("delta").mode("overwrite").save(f"{delta_base_path}/bronze/cmdb_ci")

    # 2. SILVER LAYER: Enrich Incidents with CMDB CI health & classify multi-hop ping-ponging
    silver_inc = (
        bronze_inc.join(
            bronze_cmdb.select(
                F.col("ci_name").alias("cmdb_ci"),
                F.col("is_orphan_ci"),
                F.col("mid_discovery_status"),
                F.col("os_patch_compliant"),
            ),
            on="cmdb_ci",
            how="left",
        )
        .withColumn("is_ping_pong", F.col("reassignment_count") >= F.lit(3))
        .withColumn(
            "friction_score_hours",
            F.col("mttr_hours") * (F.lit(1.0) + (F.col("reassignment_count") * F.lit(0.25))),
        )
    )
    silver_inc.write.format("delta").mode("overwrite").save(
        f"{delta_base_path}/silver/enriched_incidents"
    )

    # 3. GOLD LAYER: 80/20 Pareto Bottleneck Ranking across Subcategories
    subcat_agg = silver_inc.groupBy("category", "subcategory", "assignment_group_path").agg(
        F.count("number").alias("ticket_count"),
        F.round(F.avg("reassignment_count"), 2).alias("avg_hops"),
        F.round(F.avg("mttr_hours"), 2).alias("avg_mttr_hours"),
        F.round(F.sum("mttr_hours"), 2).alias("total_mttr_hours"),
        F.sum(F.when(F.col("sla_breached") == True, 1).otherwise(0)).alias("sla_breach_count"),  # noqa: E712
        F.sum(F.when(F.col("is_ping_pong") == True, 1).otherwise(0)).alias("ping_pong_count"),  # noqa: E712
    )

    total_window = Window.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    pareto_window = Window.orderBy(F.col("total_mttr_hours").desc()).rowsBetween(
        Window.unboundedPreceding, Window.currentRow
    )

    gold_pareto = (
        subcat_agg.withColumn("grand_total_mttr", F.sum("total_mttr_hours").over(total_window))
        .withColumn("cumulative_mttr", F.sum("total_mttr_hours").over(pareto_window))
        .withColumn(
            "cumulative_mttr_pct",
            F.round((F.col("cumulative_mttr") / F.col("grand_total_mttr")) * 100.0, 2),
        )
        .drop("grand_total_mttr", "cumulative_mttr")
    )

    gold_pareto.write.format("delta").mode("overwrite").save(
        f"{delta_base_path}/gold/pareto_queue_bottlenecks"
    )

    return {
        "bronze_incidents": bronze_inc,
        "silver_incidents": silver_inc,
        "gold_pareto": gold_pareto,
    }
