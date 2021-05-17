from altair.vegalite.v4.schema.core import Orientation
import streamlit as st
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
    try:
        st.title("Hasil Analysis Sentiment")
        df = pd.read_json('jsonfile/preprocess.json')
        c = df['Label'].value_counts()
        c_positive = c.values[0]
        c_negative = c.values[1]

        vectorizer = pickle.load(open('data/vectorizer6.pkl', 'rb'))     
        model = pickle.load(open('data/model6.pkl', 'rb'))   
        best_param = model.best_params_
        st.write("Nilai Akurasi Model: ",model.best_score_)
        metric = model.best_params_['metric']
        n_neighbors = model.best_params_['n_neighbors'].item()
        weight = model.best_params_['weights']
        dct_params = {
            'metric' : metric,
            'n_neighbors' : n_neighbors,
            'weight' : weight
        }
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

        #Grafik Double Bar Chart
        sentiment = ['Positif', 'Negatif']
        graf_chart = go.Figure(data = [
            go.Bar(name="Kamus", x=sentiment, y = [c_positive,c_negative]),
            go.Bar(name="Modeling", x=sentiment, y = [res_post,res_neg]),
        ])
        graf_chart.update_layout(barmode='group',
        title="<b>Perbandingan Komentar Kamus dengan Modelling</b>")
        st.plotly_chart(graf_chart)

        #Grafik rank word
        data_wc = df_grafik['Clean'].tolist()
        data_wc = ' '.join(data_wc)
        def Convert(string): 
            list_wc = list(string.split(" ")) 
            return list_wc
        result_wc = Convert(data_wc)
        count = Counter(word for results in result_wc for word in results.split())
        total_word = count.most_common(10)
        x_count = []
        y_word = []
        for enum in total_word:
            y_word.append(enum[0])
            x_count.append(enum[1])

        graf_rank = go.Figure(go.Bar(
            x = x_count,
            y = y_word,
            orientation = 'h'
        ))
        graf_rank.update_layout(
        title="<b> 10 Kata Paling Sering Digunakan </b>")
        st.plotly_chart(graf_rank)
    except:
        st.write("Tidak ada data dikarenakan belum melakukan scrape")
