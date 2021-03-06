from googleapiclient.http import DEFAULT_HTTP_TIMEOUT_SEC
import streamlit as st
import PIL.Image

#scrape
import os
from googleapiclient.discovery import build
import numpy as np
import pandas as pd
from streamlit.proto.Image_pb2 import Image
import time

def app():
    st.title("Hasil Scrape Data")
    gambar = PIL.Image.open('./data/example.PNG')
    st.image(gambar)
    button_recommend = st.button("Lihat Rekomendasi Saluran Youtube mengenai Ulasan Makanan")
    if button_recommend:
        st.info('''
                1.Farida Nurhan \n
                2.MGDALENAF \n
                3.Ken and Grat \n
                4.Evan Media \n
                dll
                ''')
    video_id = st.text_input("Masukkan video id ")
    try:
        start = time.time()
        st.write("Video id yang digunakan:",video_id)
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        youTubeApiKey =  "AIzaSyC2jlBOOrLdG9GKjUZzefQzVbqN0K9dhYA"
        youtube = build('youtube','v3', developerKey = youTubeApiKey)
        data_video = [["Nama", "Komentar", "Waktu", "Likes", "Reply Count"]]

        def get_all_comment(video_use):
            param_comment = youtube.commentThreads().list(part="snippet", 
                                                    videoId=video_use, 
                                                    maxResults="100", 
                                                    textFormat="plainText")
            while (True):
                data_comment = param_comment.execute()
                for i in data_comment["items"]:
                    name = i["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                    comment = i["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    published_at = i["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                    likes = i["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                    replies = i["snippet"]["totalReplyCount"]

                    data_video.append([name, comment, published_at, likes, replies])

                    totalReplyCount = i["snippet"]["totalReplyCount"]

                    if totalReplyCount > 0:
                        parent = i["snippet"]["topLevelComment"]["id"]
                        param_replies = youtube.comments().list(part="snippet", 
                                                        maxResults="100", 
                                                        parentId=parent,
                                                        textFormat="plainText")
                        data_replies = param_replies.execute()

                        for i in data_replies["items"]:
                            name = i["snippet"]["authorDisplayName"]
                            comment = i["snippet"]["textDisplay"]
                            published_at = i["snippet"]["publishedAt"]
                            likes = i["snippet"]["likeCount"]
                            replies = ""
                            data_video.append([name, comment, published_at, likes, replies])

                if 'nextPageToken' in data_comment:
                    nextToken = data_comment['nextPageToken']
                    param_comment = youtube.commentThreads().list_next(param_comment,data_comment)
                else:
                    break 
            df = pd.DataFrame({ "Nama": [i[0] for i in data_video], 
                                "Komentar": [i[1] for i in data_video], 
                                "Waktu": [i[2] for i in data_video],
                                "Likes": [i[3] for i in data_video], 
                                "Reply Count": [i[4] for i in data_video]})  
            end = time.time()
            result_time = end - start  
            st.write("Waktu: ", round(result_time,2))  
        if video_id != "":
            get_all_comment(video_id)
        
        df_data = pd.DataFrame({"Nama": [i[0] for i in data_video], 
                                "Komentar": [i[1] for i in data_video], 
                                "Waktu": [i[2] for i in data_video],})
        df_show = df_data.copy()
        df_show = df_show.drop(0)
        df = df_data.drop(['Nama','Waktu'],axis =1)
        df = df.drop(0)
        st.write("Jumlah Komentar:",len(df.index),"komentar")
        convert_df = df.reset_index().to_json('jsonfile/scrape.json', orient='records')
        st.dataframe(df_show)
        return df
    except:
        st.error("VIDEO ID TIDAK ADA")
        
