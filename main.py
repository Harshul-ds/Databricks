from pyspark.sql import SparkSession

def main():
    """
    A simple Spark job that creates a DataFrame and shows it.
    """
    spark = SparkSession.builder.appName("Cascade-Demo-Job").getOrCreate()
    print("Spark Session created successfully.")

    data = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]
    columns = ["name", "id"]
    df = spark.createDataFrame(data, columns)

    # Create a Unity Catalog schema and table, then write/read data.
    try:
        spark.sql("CREATE SCHEMA IF NOT EXISTS demo_cascade")
        df.write.mode("overwrite").saveAsTable("demo_cascade.sample_people")
        print("Data written to Unity Catalog table demo_cascade.sample_people")

        reloaded_df = spark.sql("SELECT * FROM demo_cascade.sample_people")
        print("Reloaded DataFrame from Unity Catalog:")
        reloaded_df.show()
    except Exception as e:
        print(f"Unity Catalog demo encountered an error: {e}")

    print("Sample DataFrame (original):")
    df.show()

    print("Job finished.")

if __name__ == "__main__":
    main()
