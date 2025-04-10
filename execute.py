import os
import re
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from pprint import pprint
from NL2Mongo import schema_to_mongo_nl

def load_mongo_connection():
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME")
    client = MongoClient(mongo_uri)
    return client[db_name]

def extract_pipeline(mongo_query_str):
    # Extract the aggregation pipeline array from the full MongoDB command
    match = re.search(r'\.aggregate\(\s*(\[.*\])', mongo_query_str, re.DOTALL)
    if match:
        return match.group(1)
    return mongo_query_str  # Return original if no match

def clean_mongo_syntax(js_like_query: str) -> str:
    js_like_query = re.sub(r'\n', '', js_like_query).strip()
    js_like_query = re.sub(r'([{,]\s*)(\$?\w+)\s*:', r'\1"\2":', js_like_query)
    return js_like_query

def run_mongo_query(mongo_query_str, collection):
    try:
        # Extract the pipeline array from the full query string
        pipeline_str = extract_pipeline(mongo_query_str)
        cleaned_str = clean_mongo_syntax(pipeline_str)
        pipeline = json.loads(cleaned_str)

        print("\n✅ Parsed Aggregation Pipeline:")
        pprint(pipeline)

        results = list(collection.aggregate(pipeline))
        
        if results:
            print("\n📊 Query Results:")
            pprint(results)
        else:
            print("\n⚠️ No matching documents found.")
            
            print("\n🔍 Diagnostic Information:")
            print("Diabetes field values:")
            diabetes_values = list(collection.aggregate([
                {"$group": {"_id": "$diabetes", "count": {"$sum": 1}}}
            ]))
            pprint(diabetes_values)

    except Exception as e:
        print("\n❌ Error executing Mongo query:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print("\nQuery that failed:")
        print(mongo_query_str)
        print("\nExtracted pipeline:")
        print(pipeline_str if 'pipeline_str' in locals() else "Pipeline extraction failed")

if __name__ == "__main__":
    mongo_schema = {
        "patient_records": {
            "patient_id": "string",
            "name": "string",
            "age": "int",
            "gender": "string",
            "diabetes": "yes/no",
            "blood_pressure": "yes/no",
            "arthritis": "yes/no",
            "asthma": "yes/no",
            "thyroid": "yes/no"
        }
    }

    db = load_mongo_connection()
    collection = db["patient_records"]
    
    print("\n🔍 Collection Status:")
    print(f"Collection: {collection.name}")
    print(f"Document count: {collection.count_documents({})}")
    
    nl_query = input("\n🧠 Enter a natural language question: ")
    mongo_query_str = schema_to_mongo_nl(nl_query, mongo_schema)

    print("\n🧠 Generated Mongo Query:")
    print(mongo_query_str)

    run_mongo_query(mongo_query_str, collection)