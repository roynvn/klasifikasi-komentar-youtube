from altair.vegalite.v4.schema.core import Orientation
import streamlit as st
import os
import json
import numpy as np 
import pandas as pd

#TF IDF
from sklearn.feature_extraction.text import TfidfVectorizer

#KNN
import pickle
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_validate, GridSearchCV, train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, make_scorer

#Grafik
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go

def app():
    filePath = 'jsonfile/scrape.json'
    filePath2 = 'jsonfile/preprocess.json'
    try:
        st.title("Hasil Analisis Sentimen")
        
        my_bar = st.progress(0)
        df = pd.read_json('jsonfile/preprocess.json')
        c = df['Label'].value_counts()
        c_positive = c.values[0]
        c_negative = c.values[1]
        
        vectorizer = pickle.load(open('data/use_vec.pkl', 'rb'))     
        model = pickle.load(open('data/use_model.pkl', 'rb'))   
        
        best_param = model.best_params_
        st.write("Nilai Score Model: ", round(model.best_score_*100,2),"%")
        metric = model.best_params_['metric']
        n_neighbors = model.best_params_['n_neighbors'].item()
        weight = model.best_params_['weights']
        dct_params = {
            'metric' : metric,
            'n_neighbors' : n_neighbors,
            'weight' : weight
        }
        my_bar.progress(0+25)
        st.write(dct_params)

        #Analisis Sentiment
        dummy_df = df.copy()
        dummy_df = dummy_df.drop(['level_0','Case_Fold','Tokenize','Normalisasi','Stopwords','Stemming'], axis=1)

        result = []
        result_dummy = []
        for i in range(len(dummy_df)):  
            komentar = dummy_df['Clean'][i]
            v_data = vectorizer.transform([komentar]).toarray()
            y_preds = model.predict(v_data)
            if y_preds == 1:
                result.append("Positive")
                result_dummy.append(1)
            else:
                result.append("Negative")
                result_dummy.append(0)
        dummy_df ['K-NN'] = result
        dummy_df ['dummy_value'] = result_dummy
        comparison_column = np.where(dummy_df['Label'] == dummy_df['dummy_value'], "Benar", "Salah")
        dummy_df["Hasil"] = comparison_column
        df_grafik  = dummy_df.copy()

        res_post = result.count("Positive")
        res_neg = result.count("Negative")
        st.write("Jumlah Positif:",res_post)
        st.write("Jumlah Negatif: ",res_neg)
        dummy_df = dummy_df.drop(['index','Clean','dummy_value'],axis=1)
        my_bar.progress(25+25)
        st.dataframe(dummy_df)

        #Akurasi Data
        res_true = 0
        res_false = 0
        for enum in dummy_df['Hasil']:
            if enum == "Benar": res_true += 1  
            else: res_false +=1
        res_total = len(dummy_df['Komentar'])
        st.write("Jumlah Tebakan yang benar", res_true)
        st.write("Jumlah Tebakan yang salah", res_false)
        accuracy = (res_true/res_total) * 100
        st.write("Hasil akurasinya", round(accuracy,2), "%")
        

        #Grafik Pie
        sentiment_count = dummy_df["K-NN"].value_counts()
        df_graf = pd.DataFrame({"Sentimen" :sentiment_count.index, "Label" :sentiment_count.values})

        graf = px.pie(df_graf, values = "Label", names='Sentimen',
        color_discrete_map={'Positive':'cyan', 'Negative':'royalblue'} )
        graf.update_layout(
        title="<b>Perbandingan Komentar Positif dan Negatif </b>")
        st.plotly_chart(graf)
        my_bar.progress(50+25)

        #Grafik Double Bar Chart
        sentiment = ['Positif', 'Negatif']
        graf_chart = go.Figure(data = [
            go.Bar(name="Kamus", x=sentiment, y = [c_positive,c_negative]),
            go.Bar(name="Modeling", x=sentiment, y = [res_post,res_neg]),
        ])
        graf_chart.update_layout(barmode='group',
        title="<b>Perbandingan Komentar Kamus dengan Modelling</b>")
        my_bar.progress(75+25)
        st.plotly_chart(graf_chart)
        
      
        os.remove(filePath)
        os.remove(filePath2)
        st.info("SEMUA DATA TELAH DIHAPUS")
        st.balloons()
    except:
        st.error("TIDAK ADA DATA UNTUK DILAKUKAN ANALISIS SENTIMEN DIKARENAKAN BELUM MELAKUKAN PREPROCESSING DAN LABELLING")
