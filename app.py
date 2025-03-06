import streamlit as st
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os


load_dotenv()


st.title("RAG-Based Application Using Gemini Model")


if "history" not in st.session_state:
    st.session_state.history = []
if "retriever" not in st.session_state:
    st.session_state.retriever = None


data = []  


with st.sidebar:
    st.title("Menu:")
    uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")
    if st.button("Submit & Process") and uploaded_file:
        with st.spinner("Processing..."):
            temp_file_path = f"./temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            loader = PyPDFLoader(temp_file_path)
            data = loader.load() 
            os.remove(temp_file_path)


if data:
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
    docs = text_splitter.split_documents(data)

    
    vectorstore = Chroma.from_documents(
        documents=docs, 
        embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
        persist_directory="./chroma_db"
    )
    
    
    st.session_state.retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
    st.success("Done")


query = st.chat_input("Say something: ")

if query and st.session_state.retriever:  
    st.session_state.history.append({"user": query})

    
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        "{context}"
    )

    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    
    question_answer_chain = create_stuff_documents_chain(
        ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0), 
        prompt
    )
    rag_chain = create_retrieval_chain(st.session_state.retriever, question_answer_chain)

    
    response = rag_chain.invoke({"input": query})

    
    st.session_state.history.append({"assistant": response['answer']})



if st.session_state.history:
    for chat in st.session_state.history:
        if "user" in chat:
            st.markdown(f"<div style='text-align: right; color: black;'><b>You:</b> {chat['user']}</div><br> ", unsafe_allow_html=True)
        if "assistant" in chat:
            st.markdown(f"<div style='text-align: left; color: black;'><b>Assistant:</b> {chat['assistant']}</div><br> ", unsafe_allow_html=True)