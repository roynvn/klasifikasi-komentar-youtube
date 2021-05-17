import streamlit as st

def loadpage():
    st.title("SELAMAT DATANG DI WEBSITE ANALISIS SENTIMEN MENGGUNAKAN K-NN")
    st.markdown("""
            <div>
                <p class="abstrak", align="justify">
                Website ini merupakan implementasi dari sistem Tugas Akhir yang telah dibuat
                dengan judul "Analisis Sentimen pada Komentar Video Ulasan Makanan dari Saluran
                Youtube Berbahasa Indonesia".
                Terdapat 3 menu yang dapat digunakan yaitu: </br>
                1.  Scrape </br> 
                    Untuk mengambil semua komentar dan balasan yang ada dalam video menggunakan video id.</br>
                2.  Preprocessing dan Labelling</br>
                    Untuk melakukan proses preprocessing terhadap data yang digunakan dan melakukan labelling setiap data</br>
                3.  Analisis Sentimen</br>
                    Untuk melakukan klasifikasi komentar menjadi positif atau negatif menggunakan model KNN
                    dan menampilkan grafik yang dimiliki pada data.
            </div>               
     """,unsafe_allow_html=True)
