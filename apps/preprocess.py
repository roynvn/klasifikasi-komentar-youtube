import streamlit as st
import os
import json
import pandas as pd
#from apps.scrape import app as hasil_scrape
import time

#case fold
import string
import re
import itertools

#tokenize
from nltk.tokenize import word_tokenize,MWETokenizer
from nltk.probability import FreqDist

#stopword 
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from nltk.corpus import stopwords

#stemmer
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from mpstemmer import MPStemmer


def app():
    path = 'jsonfile\scrape.json'
    path2 = 'jsonfile\preprocess.json'
    try:
        st.title("Hasil Preprocessing dan Labelling")
        df = pd.read_json('jsonfile/scrape.json')
        if df.empty:
            st.error("DATA YANG DIGUNAKAN BERSIFAT 'EMPTY' HARAP LAKUKAN SCRAPE ULANG")
        st.info("Dataset yang tersimpan: ")
        st.dataframe(df)
        button_preprocessing = st.button("Lakukan Preprocessing dan Labelling")
        button_remove = st.button("Hapus Data")
        my_bar = st.progress(0)
        
        if button_preprocessing:
            def case_fold(text):
                #Menghapus HTTP yang tidak selesai
                text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
                #menghapus kata-kata ganda
                text = re.sub(r"\b(\w+)(?:\W\1\b)+", r"\1", text, flags=re.IGNORECASE)
                # remove tab, new line, ans back slice
                text = text.replace('\\t'," ").replace('\\n'," ").replace('\\u'," ").replace('\\',"")
                # remove non ASCII (emoticon, chinese word, .etc)
                text = text.encode('ascii', 'replace').decode('ascii')
                # remove mention, link, hashtag
                text = ' '.join(re.sub("([@#][A-Za-z0-9]+)|(\w+:\/\/\S+)"," ", text).split())
                # remove incomplete URL
                text.replace("http://", " ").replace("https://", " ")
                #remove number
                text = re.sub(r"\d+", "", text)
                #remove punctuation
                text = text.translate(str.maketrans("","",string.punctuation))
                #remove whitestrip
                text = text.strip()
                #remove multiple whitespace into single whitespace
                text = re.sub('\s+',' ',text)
                #remove single char
                text = re.sub(r"\b[a-zA-Z]\b", "", text)
                #remove url
                url_pattern = re.compile(r'https?://\S+|www\.\S+')
                text = url_pattern.sub(r'', text)
                #duplicate alphabet
                #text = ''.join(alp for alp, _ in itertools.groupby(text))
                #membuat semua komentar menjadi huruf kecil 
                text = text.lower()
                return text
            def double_char(text):
                #duplicate alphabet
                text = ''.join(alp for alp, _ in itertools.groupby(text))
                return text
            def join_text(text):
                penghubung =" "
                return(penghubung.join(text))
            df['Case_Fold'] = df['Komentar'].apply(case_fold)
            my_bar.progress(0+10)
            st.success("Sukses melakukan case fold!")
            
            #TOKENIZE
            def multiword_tokenize(text):
                with open('./data/mwe.txt','r') as f:
                    mwe = [item.rstrip() for item in f]
                    
                # Initialize the MWETokenizer
                protected_tuples = [word_tokenize(word) for word in mwe]
                protected_tuples_underscore = ['_'.join(word) for word in protected_tuples]
                tokenizer = MWETokenizer(protected_tuples)
                # Tokenize the text.
                tokenized_text = tokenizer.tokenize(word_tokenize(text))
                # Replace the underscored protected words with the original MWE
                for i, token in enumerate(tokenized_text):
                    if token in protected_tuples_underscore:
                        tokenized_text[i] = mwe[protected_tuples_underscore.index(token)]
                return tokenized_text
            df['Tokenize'] = df['Case_Fold'].apply(multiword_tokenize)
            my_bar.progress(10+20)
            st.success("Sukses melakukan tokenize!")

            #NORMALISASI
            normalized_word = pd.read_excel(r'./data/normalisasi.xlsx')
            normalized_word_dict = {}
            for index, row in normalized_word.iterrows():
                if row[0] not in normalized_word_dict:
                    normalized_word_dict[row[0]] = row[1] 
            def normalized_term(text):
                return [normalized_word_dict[term] if term in normalized_word_dict else term for term in text]
            df['Normalisasi'] = df['Tokenize'].apply(normalized_term)
            my_bar.progress(30+10)
            st.success("Sukses melakukan normalisasi!")
            
            #STOPWORDS
            dump_stopwords = stopwords.words('indonesian')
            delete_stopwords = open('./data/delete_from_stopword.txt', 'r').read().split("\n")
            for enum in dump_stopwords:
                if enum in delete_stopwords:
                    dump_stopwords.remove(enum)
                    
            data_stopwords = open('./data/extend_stopword.txt', 'r').read().split("\n")
            for enum in data_stopwords:
                    dump_stopwords.append(enum)    
            list_stopwords = set(dump_stopwords)
            def stopwords_removal(text):
                return [word for word in text if word not in list_stopwords]
            df['Stopwords'] = df['Normalisasi'].apply(stopwords_removal)
            my_bar.progress(40+10)
            st.success("Sukses melakukan stopwords!")
            
            #STEMMER
            stemmer = MPStemmer()
            def stemmed_wrapper(term):
                return stemmer.stem(term)
            term_dict = {}
            for document in df["Stopwords"]:
                for term in document:
                    if term not in term_dict:
                        term_dict[term] = " "
            for term in term_dict:
                term_dict[term] = stemmed_wrapper(term) 
            # apply stemmed term to dataframe
            def get_stemmed_term(text):
                return [term_dict[term] for term in text]
            df['Stemming'] = df['Stopwords'].apply(get_stemmed_term).apply(join_text).apply(double_char).apply(multiword_tokenize).apply(normalized_term).apply(stopwords_removal)
            my_bar.progress(50+30)
            st.success("Sukses melakukan stemming")

            #Clean
            def clean_text(text):
                komentar = " "
                return (komentar.join(text))
            df['Clean'] = df['Stemming'].apply(clean_text)
            my_bar.progress(80+10)
            st.success("Sukses melakukan clean!")

            #LABELING
            items_komen = df['Stemming']
            df_pos = pd.read_csv(r'./data/New-Positif.csv')
            df_neg = pd.read_csv(r'./data/New-Negatif.csv')
            hasil = []
            for item in items_komen:
                count_p = 0
                count_n = 0
                for kata_pos in df_pos['word']:          
                    if kata_pos.strip() in item:
                        print("Kata positif= ", kata_pos)
                        pos = df_pos.loc[df_pos['word'] == kata_pos, 'weight'].values.item()
                        count_p += pos
                    elif kata_pos.strip() not in item:
                        count_p += 0   
                for kata_neg in df_neg['word']:
                    if kata_neg.strip() in item:
                        print("Kata negatif= ", kata_neg)
                        neg = df_neg.loc[df_neg['word'] == kata_neg, 'weight'].values.item()
                        count_n += neg
                    elif kata_neg.strip() not in item:
                        count_n += 0  
                print(item)
                print("count_p =", count_p)
                print("count_n =", count_n)
                result = count_p + count_n
                print("Result= ", result)
                print('='*50)
                if result > 0:
                    hasil.append(1)
                elif result < 0:
                    hasil.append(0)
                else:
                    hasil.append(-1)
            df['Label'] = hasil
            indexNames = df[df['Label'] == -1 ].index
            df.drop(indexNames , inplace=True)
            c = df['Label'].value_counts()
            c_positive = c.values[0]
            c_negative = c.values[1]
            my_bar.progress(90+10)
            st.success("Sukses melakukan labelling!")
            st.write("Jumlah Positif:",c_positive)
            st.write("Jumlah Negatif: ",c_negative)
            convert_df = df.reset_index().to_json('jsonfile/preprocess.json', orient='records')
            st.dataframe(df)
            st.info('Label 1: Positif dan Label 0: Negatif')
            return df

        elif button_remove:
            os.remove(path)
            os.remove(path2)
            st.error("Dataset telah dihapus")
            df_empty = pd.DataFrame({'Komentar' : []})
            st.dataframe(df_empty)
            st.empty()

    except:
        st.error("TIDAK ADA DATA UNTUK DILAKUKAN PREPROCESSING DAN LABELLING DIKARENAKAN BELUM MELAKUKAN SCRAPE")