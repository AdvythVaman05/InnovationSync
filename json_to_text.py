import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate




def json_to_text(json_in: dict ):
    
    load_dotenv()

    groq_api_key=os.getenv("GROQ_API_KEY")
    
    
    # Flattening the json to nake it easier to work with 
    text=[]
    def flat_json(inp,prefix=""):
        
        for k,v in inp.items():
            if isinstance(v,dict):
                flat_json(v,prefix+k+': ')
            elif isinstance(v,list):
                for i,item in enumerate(v):
                    flat_json({f"{k}[{i}]":item},prefix)
            else:
                text.append(f"{prefix}{k}: {v}")
    
    flat_json(json_in) 
    
    
    
    docs=[Document(page_content=text) for text in text] 
    embedding_model= HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vect_store=FAISS.from_documents(docs,embedding_model)
    print(vect_store)
    
    retriever=vect_store.as_retriever(Ssarch_kwargs={"k":3}) 
    
    
    # Loading the model
    
    llm=ChatGroq(api_key=groq_api_key,model='llama3-70b-8192')
    
    
    # Giving the prompt 
    
    prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an intelligent assistant. Given the context below, produce a concise, structured, and meaningful summary in natural language.

Avoid restating the structure of the input. Instead, focus on interpreting the data like a profile or a description. Keep it formal and clear.

Context:
{context}

Question: {question}

Answer:
"""
)


    qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)

    
    response = qa_chain.invoke({"query": "Summarize the data in a clean, structured paragraph using natural language."})
    return response["result"]


    
                
            


