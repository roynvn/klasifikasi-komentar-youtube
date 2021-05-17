#app.py
import streamlit as st
from multiapp import MultiApp
from apps import homepage,scrape, preprocess, analysisentiment


app = MultiApp()


#TAMBAHKAN SEMUA APPS YANG TELAH DIBUAT
app.add_app("Homepage",homepage.loadpage)
app.add_app("1.Scrape", scrape.app)
app.add_app("2.Preprocessing dan Labelling", preprocess.app)
app.add_app("3.Analisis Sentiment", analysisentiment.app)

#RUN APP
app.run()
