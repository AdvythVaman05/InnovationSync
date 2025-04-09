import os
import re
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from pprint import pprint


def load_mongo_connection():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "test")
    collection_name = os.getenv("COLLECTION_NAME", "titanic")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    return collection


def get_collection_fields(collection):
    # Get one sample document and extract its keys (field names)
    sample = collection.find_one()
    if not sample:
        return []
    return list(sample.keys())


def clean_mongo_syntax(js_like_query: str) -> str:
    """
    Convert JavaScript-style MongoDB query to valid JSON.
    Quotes all keys (including $operators) and ensures JSON compatibility.
    """
    # Remove newlines and extra whitespace
    js_like_query = re.sub(r'\n', '', js_like_query).strip()

    # Quote all unquoted keys (including $operators)
    js_like_query = re.sub(r'([{,]\s*)(\$?\w+)\s*:', r'\1"\2":', js_like_query)

    return js_like_query


def fix_field_case(pipeline_str, actual_fields):
    """
    Replace lowercase field names in the query with actual field names from MongoDB.
    """
    for field in actual_fields:
        # Replace fields like "$age" or "_id: $parch"
        pattern = re.compile(rf'(\$|["\s]){field.lower()}(["\s]|[^\w])', re.IGNORECASE)

        def replacement(match):
            return match.group(1) + field + match.group(2)

        pipeline_str = pattern.sub(replacement, pipeline_str)
    return pipeline_str



def extract_pipeline(mongo_query_str: str):
    if mongo_query_str.startswith("db.") and ".aggregate(" in mongo_query_str:
        pipeline_start = mongo_query_str.find(".aggregate(") + len(".aggregate(")
        pipeline_end = mongo_query_str.rfind(")")
        return mongo_query_str[pipeline_start:pipeline_end]
    return None


def run_mongo_query(mongo_query_str, collection):
    try:
        pipeline_str = extract_pipeline(mongo_query_str)
        if not pipeline_str:
            print("❌ Couldn't extract pipeline.")
            return

        # Get actual field names from collection
        actual_fields = get_collection_fields(collection)

        # Fix field name casing
        pipeline_str = fix_field_case(pipeline_str, actual_fields)

        # Clean and prepare JSON-like string
        cleaned_str = clean_mongo_syntax(pipeline_str)

        # Convert to valid Python object
        pipeline = json.loads(cleaned_str)

        print("✅ Parsed aggregation pipeline:")
        pprint(pipeline)

        # Run aggregation
        results = collection.aggregate(pipeline)
        print("\n📊 Results:")
        result_found = False
        for doc in results:
            pprint(doc)
            result_found = True

        if not result_found:
            print("⚠️ No matching documents found.")

    except Exception as e:
        print("❌ Error executing Mongo query:")
        print(e)


if __name__ == "__main__":
    # Sample MongoDB query string generated from LLM
    mongo_query_str = '''db.titanic.aggregate([
        { $group: { _id: "$parch", avgAge: { $avg: "$age" } } },
        { $match: { avgAge: { $lt: 21 } } }
    ])'''

    print("🧠 Generated Mongo Query String:")
    print(mongo_query_str)

    collection = load_mongo_connection()
    run_mongo_query(mongo_query_str, collection)
