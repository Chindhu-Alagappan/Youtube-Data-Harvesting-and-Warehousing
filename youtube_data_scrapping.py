# Import necessary packages
import streamlit as st
import googleapiclient.discovery
from pprint import pprint
import pymongo
import mysql.connector
import isodate
import pandas as pd 
import plotly.express as px

# --------------Retrieving data from youtube API---------------

# scrapping channel details
def ScrapChannelDetails(response,channel_details):
    channel_details["channel_name"] = response['items'][0]['snippet']['title']
    channel_details["channel_id"] = response['items'][0]['id']

    channel_details["subscriber_count"] = \
        response['items'][0]['statistics']['subscriberCount']
    
    channel_details["channel_views"] = \
        response['items'][0]['statistics']['viewCount']
    
    channel_details["channel_desc"] = \
        response['items'][0]['snippet']['description']
    
    channel_details["playlist_id"] = \
        response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    return channel_details

# scrapping comment details for each video
def ScrapCommentDetails(youtube,videoID,comment_detail):
    try:
        request = youtube.commentThreads().list(
            part = "snippet,replies",
            maxResults = 200,
            videoId = videoID
        )
        response = request.execute()
        for index in range(0,len(response['items'])):
            ref_name = "comment_id_"+str(index+1)
            comment_detail[ref_name] = {}

            comment_detail[ref_name]['comment_id'] = \
                response['items'][index]['snippet']['topLevelComment']['id']
            
            comment_detail[ref_name]['comment_text'] = \
                response['items'][index]['snippet']['topLevelComment']['snippet']['textOriginal']
            
            comment_detail[ref_name]['comment_author'] = \
                response['items'][index]['snippet']['topLevelComment']['snippet']['authorDisplayName']
            
            comment_detail[ref_name]['comment_published_at'] = \
                response['items'][index]['snippet']['topLevelComment']['snippet']['publishedAt']
            
        return comment_detail
        
    except Exception as e:
        print('Unable to retrieve comments for video : '+str(videoID))
        print('Error Message'+str(e))

#  fetching all video ids from a playlist
def GetVideoIdsFromPlaylist(youtube,playListID):
    nextPT = ""
    total_videos = 0
    batch_video_ids = []
    while True:
        request = youtube.playlistItems().list(
            part = "snippet,contentDetails",
            maxResults = 50,
            playlistId = playListID,
            pageToken = nextPT
        )
        response = request.execute()
        video_ids = []
        for i in range(0,len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])
        batch_video_ids.append(video_ids)
        total_videos += len(video_ids)
        nextPT = response.get('nextPageToken')
        if not nextPT:
            break
    
    return batch_video_ids

# scrapping video details   
def ScrapVideoDetails(youtube,response,video_detail,index):
    video_detail["video_id"] = response['items'][index]['id']
    video_detail["video_name"] = response['items'][index]['snippet']['title']

    video_detail["video_description"] = \
        response['items'][index]['snippet']['description']
    
    video_detail["tags"] = response['items'][index]['snippet'].get('tags')

    video_detail["published_at"] = \
        response['items'][index]['snippet']['publishedAt']
    
    video_detail["view_count"] = \
        response['items'][index]['statistics']['viewCount']
    
    video_detail["like_count"] = \
        response['items'][index]['statistics'].get('likeCount')
    
    video_detail["favorite_count"] = \
        response['items'][index]['statistics']['favoriteCount']
    
    video_detail["comment_count"] = \
        response['items'][index]['statistics'].get('commentCount')
    
    video_detail["duration"] = \
        response['items'][index]['contentDetails']['duration']
    
    video_detail["thumbnail"] = \
        response['items'][index]['snippet']['thumbnails']['default']['url']
    
    caption_status = response['items'][index]['contentDetails']['caption']

    video_detail["caption_status"] = \
        "Not Available" if caption_status==False else "Available"
    
    video_detail["comments"] = {}

    video_detail["comments"] = \
        ScrapCommentDetails(youtube,video_detail["video_id"],video_detail["comments"])
    
    return video_detail

# receiving channel id from user
def GetChannelIds(youtube,channelID,status):
    channel_info = []
    status.write('Connecting and scrapping data from ChannelD : ' + channelID)
    channel = {}

    try:
        request = youtube.channels().list(
            part = "snippet,contentDetails,statistics",
            id = channelID
        )
        response = request.execute()

        channel['channel_id'] = channelID
        channel['channel_details'] = {}
        channel['channel_details'] = \
            ScrapChannelDetails(response,channel['channel_details'])
        
        playlist_id = channel['channel_details']["playlist_id"]
        video_ids= GetVideoIdsFromPlaylist(youtube,playlist_id)
        vi = 1
        channel['video_details'] = {}
        for video_batch in video_ids:
            request = youtube.videos().list(
                part = "snippet,contentDetails,statistics",
                id = video_batch
            )
            response = request.execute()
            for i in range(0,len(response['items'])):
                ref_name = "video_id_"+str(vi)
                vi += 1
                channel["video_details"][ref_name] = {}
                channel["video_details"][ref_name] = \
                    ScrapVideoDetails(youtube,
                                      response,
                                      channel["video_details"][ref_name],
                                      i)
        
        channel_info.append(channel)

        return channel_info
    
    except Exception as e:
        status.write("Unable to scrap data from channel : " + channelID)
        print("Unable to scrap data from channel : " + channelID)
        return -1

# --------------Data Insertion / Updation into MongoDB ---------------

def MigratingDataToMongoDb(table,data):
    flag = 0

    query = {'channel_id':data[0]['channel_id']}
    project = {'channel_id':1}
    res = table.find(query,project)
    for i in res:
        table.update_one({'channel_id':i['channel_id']},
                         {"$set":{'channel_details':data[0]['channel_details'],
                                  'video_details':data[0]['video_details']}})
        flag = 1

    if(flag == 0):
        table.insert_one(data[0])
        flag = 1

# --------------Data Insertion / Updation into MySQL ---------------

# parsing duration to seconds format
def parse_duration(duration):
    dur = isodate.parse_duration(duration)
    return dur.total_seconds()

# parsing date from string to datetime format
def parse_date(published_date):
    return isodate.parse_datetime(published_date)

# inserting / updating channel details in sql
def AppendChannelDetails(mycursor,channel_details,isPresent):
    if (isPresent):
        query = '''UPDATE channel SET channel_name=%s, 
                                channel_views=%s, 
                                channel_description=%s, 
                                channel_subscibers=%s 
                                where channel_id=%s'''
        data = (
            channel_details['channel_name'],
            int(channel_details['channel_views']),
            channel_details['channel_desc'],
            int(channel_details['subscriber_count']),
            channel_details['channel_id'],
        )
    else:
        query = 'INSERT INTO channel values (%s,%s,%s,%s,%s)'
        data = (
            channel_details['channel_id'],
            channel_details['channel_name'],
            int(channel_details['channel_views']),
            channel_details['channel_desc'],
            int(channel_details['subscriber_count'])
        )
    mycursor.execute(query,data)

# inserting / updating video and comment details in sql
def AppendVideoAndCommentDetails(mycursor,
                                 video_details,
                                 playlist_id,
                                 channel_id,
                                 isPresent):
    if (isPresent):
        query = """DELETE FROM comment where video_id IN 
            (SELECT video_id from video as v WHERE v.channel_id=%s)"""
        data = (channel_id,)
        mycursor.execute(query,data)
        query = 'DELETE FROM video where channel_id=%s'
        data = (channel_id,)
        mycursor.execute(query,data)
        
    for video in video_details.keys():
        duration = parse_duration(video_details[video]['duration'])
        pub_date = parse_date(video_details[video]['published_at'])
        like_count = video_details[video]['like_count']
        com_count = video_details[video]['comment_count']
        query = """ INSERT INTO video values
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
        data = (
            video_details[video]['video_id'],
            playlist_id,
            video_details[video]['video_name'],
            video_details[video]['video_description'],
            pub_date,
            int(video_details[video]['view_count']),
            int( 0 if like_count is None else like_count),
            int(video_details[video]['favorite_count']),
            int(0 if com_count is None else com_count),
            duration,
            video_details[video]['thumbnail'],
            video_details[video]['caption_status'],
            channel_id
        )
        mycursor.execute(query,data)

        if(video_details[video]['comments'] is None):
            continue
            
        for comment in video_details[video]['comments'].keys():

            com_pub_date = \
            parse_date(video_details[video]['comments'][comment]['comment_published_at'])

            query = 'INSERT INTO comment values (%s,%s,%s,%s,%s)'
            data = (
                video_details[video]['comments'][comment]['comment_id'],
                video_details[video]['video_id'],
                video_details[video]['comments'][comment]['comment_text'],
                video_details[video]['comments'][comment]['comment_author'],
                com_pub_date,
            )
            mycursor.execute(query,data)

# checking if the received channel (from user) is present in sql or not
def MigratingDataToMySQL(mycursor,channel_data):
    query = 'select count(*) from channel where channel_id=%s'
    data = (channel_data[0]['channel_id'],)
    mycursor.execute(query,data)
    isPresent = 0
    for i in mycursor:
        isPresent = i[0]
    AppendChannelDetails (mycursor,
                         channel_data[0]['channel_details'],
                         isPresent)
    AppendVideoAndCommentDetails(mycursor,
                                 channel_data[0]['video_details'],
                                 channel_data[0]['channel_details']['playlist_id'],
                                 channel_data[0]['channel_id'],
                                 isPresent)

# -------------- Query Execution in MySQL ---------------

def ExecuteQuery(mycursor,query):
    mycursor.execute(query)
    res=mycursor.fetchall()
    field_headings=[i[0] for i in mycursor.description]
    return pd.DataFrame(res,columns=field_headings)

# -------------- Main Method ---------------

def main():
    
    # connecting to google API
    api_service_name = "youtube"
    api_version = "v3"
    apiKey = "AIzaSyD2kKq3EbMlQr1jAqc-DqTJbkp15aE-o24"
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=apiKey)
    
    # connecting with mongo DB
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["youtubedatascrapping"]
    table = db["channel"]

    #Connecting with MYSQL
    mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'Chinka@SQL123',
        db = 'youtubedatascrapping'
    )
    mycursor = mydb.cursor()

    # streamlit page setup
    st.set_page_config(
        page_title = "Youtube Data Harvesting",

        page_icon = \
            ":black_right_pointing_triangle_with_double_vertical_bar:",

        initial_sidebar_state = "collapsed"
        )
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Home", 
                                            "About", 
                                            "Query", 
                                            "View", 
                                            "Visualize"])

    # streamlit portal design
    # "Home" tab population
    with tab1:
        st.header("Youtube Data Harvesting and Warehousing")
        channel_id_value = st.text_input('Enter the Channel ID to Scrap')
        if(channel_id_value != ""):
            if(st.button('Scrap')):
                status = st.empty()
                channel_data = GetChannelIds(youtube,channel_id_value,status)
                if(channel_data != -1):
                    status.write(":green[Scrapped Data Successfully]")
                    with st.expander("View JSON Format"):
                        st.json(channel_data)
                    MigratingDataToMongoDb(table,channel_data)
                    MigratingDataToMySQL(mycursor,channel_data)
                    mydb.commit()

    # "About" tab population
    with tab2:
        st.header("About")
        st.write("""Want to scrap details of any youtube channel and analyse
                 the data in it - Here you go... This portal aims at
                 scrapping the youtube channel details with channel ID.
                 Also, it provides the room for querying, viewing and
                 visualizing  the channel data scrapped.\n""")
        st.write("""Developed by Chindhu as an open-source project for
                 efficiently collecting, storing and analyzing youtube data
                 using Python, MongoDB and MySQL tech stacks. Do leave your
                 suggestions or bottle necks while using the portal, so that
                 it can be revised and improved.\n""")
        st.write('Email - chindhual@gmail.com')

    # "Query" tab population   
    with tab3:
        st.header("Query")
        map_query_options = {
            '1) What are the names of all the videos and their corresponding\
                  channels?':
            'SELECT v.video_name,c.channel_name FROM video as v INNER JOIN \
                channel as c ON c.channel_id=v.channel_id',

            '2) Which channels have the most number of videos, \
                    and how many videos do they have?':
            """SELECT c.channel_name,COUNT(v.video_id) as video_count \
                FROM video as v INNER JOIN channel as c \
                ON c.channel_id=v.channel_id GROUP BY c.channel_name \
                ORDER BY video_count DESC LIMIT 1""",

            '3) What are the top 10 most viewed videos and their respective\
                  channels':
            """SELECT v.video_name,v.view_count,c.channel_name \
                FROM video as v INNER JOIN channel as c \
                ON c.channel_id=v.channel_id ORDER BY v.view_count DESC \
                LIMIT 10""",

            '4) How many comments were made on each video, \
                    and what are their corresponding video names?':
            'SELECT v.video_name,v.comment_count FROM video as v',

            '5) Which videos have the highest number of likes, \
                and what are their corresponding channel names?':
            """SELECT v.video_name,v.like_count,c.channel_name \
                FROM video as v INNER JOIN channel as c ON c.channel_id=v.channel_id
                ORDER BY v.like_count DESC LIMIT 10""",

            """6) What is the total number of likes and dislikes for each video, 
            and what are their corresponding video names?""":
            'SELECT v.video_name,v.like_count  FROM video as v',

            """7) What is the total number of views for each channel, 
                and what are their corresponding channel names?""":
            """SELECT c.channel_name,SUM(v.view_count) as total_views \
                FROM channel as c INNER JOIN video as v ON \
                c.channel_id=v.channel_id GROUP BY c.channel_name""",

            '8) What are the names of all the channels that have published \
                videos in the year 2022?':
            """SELECT c.channel_name, COUNT(YEAR(v.published_date)) as \
                count_of_videos_uploaded FROM channel as c INNER JOIN video \
                as v ON v.channel_id=c.channel_id WHERE YEAR(v.published_date)="2022" \
                GROUP BY c.channel_name""",

            """9) What is the average duration of all videos in each channel, 
                and what are their corresponding channel names?""":
            """SELECT c.channel_name, AVG(v.duration) as average_duration \
                FROM channel as c INNER JOIN video as v ON c.channel_id=v.channel_id \
                GROUP BY c.channel_name""",

            """10) Which videos have the highest number of comments, 
                and what are their corresponding channel names?""":
            """SELECT c.channel_name,v.video_name,v.comment_count \
                FROM video as v INNER JOIN channel as c ON c.channel_id=v.channel_id \
                ORDER BY v.comment_count DESC LIMIT 10"""
        }
        sql_query = st.selectbox('Select query from drop down menu...', 
                                 map_query_options.keys())
        query = map_query_options[sql_query]
        df = ExecuteQuery(mycursor,query)
        if not df.empty:
            st.dataframe(df)
        else:
            st.write("No Results Found !")

    # "View" tab population
    with tab4:
        st.header("View")
        tables = st.multiselect('Select table(s) to display',
                                ['Channels', 'Videos', 'Comments'])
        if(tables):
            if(st.button('View Table')):
                for table in tables:
                    if table == 'Channels':
                        query = 'SELECT * FROM channel'
                        st.write(":blue[Channel Details]")
                        st.dataframe(ExecuteQuery(mycursor,query))
                    if table == 'Videos':
                        query = 'SELECT * FROM video'
                        st.write(":blue[Video Details]")
                        st.dataframe(ExecuteQuery(mycursor,query))
                    if table == 'Comments':
                        query = 'SELECT * FROM comment'
                        st.write(":blue[Comment Details]")
                        st.dataframe(ExecuteQuery(mycursor,query))

    # "Visualize" tab population             
    with tab5:
        st.header("Visualize")

        query = 'SELECT channel_name,channel_subscibers FROM channel'
        df = ExecuteQuery(mycursor,query)
        st.write("Scatter plot representing channel with subsciber count :")
        st.scatter_chart(data=df, x='channel_name', y='channel_subscibers')
    
        query = """SELECT c.channel_name,COUNT(v.video_id) as total_videos_uploaded FROM channel as c 
                INNER JOIN video as v ON c.channel_id=v.channel_id GROUP BY c.channel_name"""
        df = ExecuteQuery(mycursor,query)
        st.write("Bar chart representing channel with total videos uploaded :")
        st.bar_chart(data=df, x='channel_name', y='total_videos_uploaded')

        query='select channel_name,channel_views from channel;'
        df = ExecuteQuery(mycursor,query)
        st.write("Line chart representing channel with total channel views :")
        st.line_chart(data=df, x='channel_name', y='channel_views')

    # adding CSS to tabs
    css = '''
        <style>
            .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
             font-size:1rem;
            }
        </style>
        '''
    st.markdown(css, unsafe_allow_html=True)

if __name__ == "__main__":
    main()