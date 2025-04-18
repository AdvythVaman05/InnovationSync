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
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vect_store = FAISS.from_documents(docs, embedding_model)
    retriever = vect_store.as_retriever(search_kwargs={"k": 4})

    llm = ChatGroq(api_key=groq_api_key, model='llama3-70b-8192')
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a MongoDB expert. Based on the schema provided and the user's natural language question, 
generate ONLY the MongoDB aggregation pipeline in valid JSON format.

Important: 
- Return ONLY the aggregation pipeline array in JSON format
- Do not include any explanations or markdown formatting
- For yes/no fields like diabetes, use: {{"$regex": "^yes$", "$options": "i"}}
- Ensure all field names are properly quoted
- Use proper MongoDB syntax for all operators

Schema Context:
{context}

Natural Language Question: {question}

ONLY return the aggregation pipeline array in JSON format:
"""
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )

    response = qa_chain.invoke({"query": nl_query})
    return response["result"]