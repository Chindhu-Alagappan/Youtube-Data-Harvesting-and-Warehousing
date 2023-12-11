# Youtube-Data-Harvesting-and-Warehousing
This is an open-source project repo which deals with youtube data scrapping, analyzing and visualizing using python, mongodb, mysql and streamlit.

## Introduction
Youtube is a popular online video sharing and social media platform owned and operated by Google. This project aims at scrapping youtube data lake with channel ID, querying and visualizing the data by creating a Streamlit application.

## Table of Contents
1. Pre-requisites
2. Technology Stacks 
3. Usage
4. Project Workflow
5. Data Scapping
6. Storing in MongoDB
7. Migrating to MySQL
8. Querying
9. Viewing and Visualization
10. Further Improvements

## Pre-requsites
Install the following packages to run the project. 
```
pip install streamlit
pip install google-api-python-clien
pip install pymongo
pip install mysql-connector-python
pip install isodate
pip install pandas
pip install plotly-express
```

## Technology Stack
- Python scripting 
- NoSQL - MongoDB
- SQL - MySQL
- Streamlit App development
- API Integration - Google API

## Usage
Clone the repo from the below mentioned link.  
[Youtube-Data-Harvesting-and-Warehousing](https://github.com/Chindhu-Alagappan/Youtube-Data-Harvesting-and-Warehousing.git)  
Install packages from "requirement.txt"  
Run the streamlit application using `streamlit run .\youtube_data_scrapping.py`  
View the portal in your [localhost](http://localhost:8501/)  

## Project Workflow
The below diagram depicts the flowchart of the youtube data analysis.  
![YoutubeProjectFlow](https://github.com/Chindhu-Alagappan/Youtube-Data-Harvesting-and-Warehousing/blob/1d653b916b6fe4644bb11e49bb5ace72f2440900/YoutubeProjectFlow.png)   

## Data Scrapping 
The project uses Google API key to connect with youtube API and fetch the all details about the channel, given the channel ID. Further the data scrapped is presented in JSON format to users of the streamit application.

## Storing in MongoDB 
Connecting python with mongoDB using credentials allows us to store data in NoSQL format. Initally, we prepare the data by extracting the required features in channel, video and comments section of the JSON document. Later, we perform a query to check if the channel scrapped already exists in MongoDB or not. If it is avaiable, we are going to update the document with the specified channelID. Else, we insert the channel information as a new document into NoSQL. 

## Migrating to MySQL 
Again, the data has to converted from unstructured to structured format in order to store in MySQL. Connection must to be established between python and MySQL using mysql.connector package.
We have already created 3 tables in the backend called *channel*, *video* and *comment*. The tables have been described below.

**Table : Channel**
| Column Name | Data Type | Description |
| :---------- | :-------- | :---------- |
| channel_id | VARCHAR(255) | Unique identifier of the channel |
| channel_name | VARCHAR(255) | Name of channel |
| channel_views | INT  | Total views for the channel |
| channel_desc | TEXT | Description of the channel |
| channel_subscibers | INT | Total channel subscibers |

**Table : Video**
| Column Name | Data Type | Description |
| :---------- | :-------- | :---------- |
| video_id | VARCHAR(255) | Unique identified of the video |
| playlist_id | VARCHAR(255) | Default playlist ID for each channel |
| video_name | VARCHAR(255) | Name of the video |
| video_description | VARCHAR(255) | Description of the video |
| published_date | DATETIME | Date time at which the video is published |
| view_count | INT | Total views for the video |
| like_count | INT | Total likes for the video |
| favorite_count | INT | Total no.of viewers who marked the video as favorite |
| comment_count | INT | Total comments for the video |
| duration | INT | Duration of the vidoe in seconds |
| thumbnail | VARCHAR(255) | Link of the thumbnail image |
| caption_status | VARCHAR(255) | Caption status of the video |
| channel_id | VARCHAR(255) | Foreign key from channel table |

**Table : Comment**
| Column Name | Data Type | Description |
| :---------- | :-------- | :---------- |
| comment_id | VARCHAR(255) | Unique Identifier of the comment |
| video_id | VARCHAR(255) | Foreign key from video table |
| comment_text | VARCHAR(255) | Text of the comment |
| comment_author | VARCHAR(255) | Author of the comment |
| comment_published_date | VARCHAR(255) | Comment published date |

## Querying
There exists 10 pre-defined queries in "Query" tab of the portal. Choosing any one from the select box allows us to query the tables accordingly.

## Viewing and Visualizing 
We can view the 3 tables (channel, video and comment) present in SQL in the streamlit application by Navigating to the "View" tab.  
Also, streamlit visualization functions help us understand the power of visualization by plotting scatter plots, bar charts and line graphs in the "Visualize" tab.

## Further Improvements 
The project can further be enhanced by performing sentimental analysis on the video description and comments extracted for each video. This will help us to better understand and organize the genere of the video published, which in turn can be given as a recommendation for the preferred age group of viewers.  
If you encounter any issues or have suggestions for improvements, feel free to reach out.  
  
Email : *chindhual@gmail.com*  
LinkedIn : *https://www.linkedin.com/in/chindhu-alagappan-57605112a/*
  
Thanks for showing interest in this repository ! 



