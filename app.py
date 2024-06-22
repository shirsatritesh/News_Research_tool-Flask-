from flask import Flask, request, render_template, redirect, url_for

import os
import pickle
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv() 
#load openAI api key


file_path = "faiss_store_openai.pkl"

llm = ChatOpenAI(temperature=0.9, max_tokens=500, model="gpt-4")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_urls', methods=['POST'])
def process_urls():
    urls = [request.form['url1'], request.form['url2'], request.form['url3']]
    
    # Load data
    loader = UnstructuredURLLoader(urls=urls)
    data = loader.load()
    
    # Split data
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000
    )
    docs = text_splitter.split_documents(data)
    
    # Create embeddings and save them to FAISS index
    embeddings = OpenAIEmbeddings()
    vectorstore_openai = FAISS.from_documents(docs, embeddings)
    
    with open(file_path, "wb") as f:
        pickle.dump(vectorstore_openai, f)
    
    return redirect(url_for('index'))

@app.route('/query', methods=['POST'])
def query():
    query = request.form['question']
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            vectorstore = pickle.load(f)
        
        chain = RetrievalQAWithSourcesChain.from_llm(llm=llm, retriever=vectorstore.as_retriever())
        result = chain({"question": query}, return_only_outputs=True)
        
        answer = result["answer"]
        sources = result.get("sources", "").split("\n")
        
        return render_template('index.html', answer=answer, sources=sources)
    
    return render_template('index.html', answer="No data processed yet. Please provide URLs first.", sources=[])

if __name__ == '__main__':
    app.run(debug=False)
