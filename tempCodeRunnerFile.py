import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def schema_to_mongo_nl(nl_query: str, mongo_schema: dict):
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")

    # Flatten schema for context (like field names, collections etc.)
    flat_schema = []

    def flatten_schema(inp, prefix=""):
        for k, v in inp.items():
            if isinstance(v, dict):
                flatten_schema(v, prefix + k + '.')
            elif isinstance(v, list):
                flatten_schema(v[0], prefix + k + '[].')
            else:
                flat_schema.append(f"{prefix}{k}: {v}")

    flatten_schema(mongo_schema)

    docs = [Document(page_content=line) for line in flat_schema]

    # Embed the schema for retrieval
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vect_store = FAISS.from_documents(docs, embedding_model)
    retriever = vect_store.as_retriever(search_kwargs={"k": 4})

    # LLM setup
    llm = ChatGroq(api_key=groq_api_key, model='llama3-70b-8192')

    # Prompt template
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a MongoDB expert. Based on the schema provided and the user's natural language question, generate the most accurate MongoDB query.

Make sure the query follows the MongoDB syntax, uses correct fields, and handles filtering, projection, and conditions correctly. Just give the query, nothing else.

Schema Context:
{context}

Natural Language Question: {question}

MongoDB Query:
"""
    )

    # Retrieval-based QA
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )

    response = qa_chain.invoke({"query": nl_query})
    return response["result"]


if __name__ == "__main__":
    # This schema is illustrative based on your titanic dataset
    mongo_schema = {
        "titanic": {
            "_id": "ObjectId",
            "passengerid": "int",
            "survived": "int",
            "pclass": "int",
            "name": "string",
            "sex": "string",
            "age": "double",
            "sibsp": "int",
            "parch": "int",
            "ticket": "string",
            "fare": "double",
            "cabin": "string",
            "embarked": "string"
        }
    }

    textual_query = '''mongo: which cabinet has average age less than 21? | titanic : _id, passengerid, survived, pclass, name, sex, age, sibsp, parch, ticket, fare, cabin, embarked'''

    # Extract the natural language part from textual_query
    nl_query = textual_query.split("mongo:")[1].split("|")[0].strip()

    mongo_query = schema_to_mongo_nl(nl_query, mongo_schema)

    from pprint import pprint
    pprint(mongo_query)
