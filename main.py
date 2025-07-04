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

    print("Sample DataFrame:")
    df.show()

    print("Job finished.")

if __name__ == "__main__":
    main()
