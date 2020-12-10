
from flask import Flask
from flask import render_template
from datetime import datetime
import re
import requests



import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import time

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, TYER
from mutagen.easyid3 import EasyID3
import youtube_dl
import urllib.request
from bs4 import BeautifulSoup
import os
import subprocess
import shutil


from selenium import webdriver 
import pandas as pd 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC



app = Flask(__name__)


# old flask tutorial
@app.route("/hello1/<name>")
def hello_there1(name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")

    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    match_object = re.match("[a-zA-Z]+", name)

    if match_object:
        clean_name = match_object.group(0)
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return content


# old flask tutorial
@app.route("/hello/")
@app.route("/hello/<name>")
def hello_there(name = None):
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )

# old flask tutorial
@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")

# remove special chars from string
def cleanString(text):
    return "".join([i for i in text if i not in [i for i in '/\\:*?"><|']])

# used by donwloadyoutubtomp3
def checkDownloadCallback(d):
    if '_percent_str' in d:
        if d['status'] == 'downloading':
            print ("\r" + d['_percent_str'], end='')
    if d['status'] == 'finished':
            print ('\rDone downloading, now converting ...')

#used by downloadyoutube.mp3
class logErrors(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print (msg)

def downloadYoutubeToMP3(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best[ext=m4a]/mp4',
            'postprocessors': [{ 'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', }],
            'logger': logErrors(),
            'progress_hooks': [checkDownloadCallback]
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            a = ydl.download([link])
        return True
    except Exception as e:
        print (repr(e))
        return False


# project code
@app.route("/playlist/")
@app.route("/playlist/<name>")
def playlistCall(name = None):
#name is ID of spotify playlist

    #json has my developer account name and password
    with open('settings.json') as data_file:
        settings = json.load(data_file)

    client_credentials_manager = SpotifyClientCredentials(client_id=settings['spotify']['client_id'], client_secret=settings['spotify']['client_secret'])
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.trace=False

    print("Starting Back-end")

    song_data = {} # song_data[uri] = {'artist':x, 'album':x, 'title':x, 'ablum_art':x, 'track':x}
    individual_songs = []

# testList - 6eDcgr3PC5EOqa2k0ApB9p
    print(name)

    username = "shamilian" 
    playlist_id = name 
    offset = 0
    saveNum=0
    passName = ["" for x in range(10)]
    outputDir = os.getcwd() + "/static/outputDir/"
    print("Cleaning Dir " + outputDir)
    # delete the old stuff
    shutil.rmtree(outputDir, ignore_errors=True, onerror=None) 

    print("Fetching playlist" )
    results = sp.user_playlist_tracks(username, playlist_id, offset=offset)
    individual_songs += results['items']
    while (results['next'] != None):
        offset += 100
        results = sp.user_playlist_tracks(username, playlist_id, offset=offset)
        individual_songs += results['items']
    print("Song List Done")

    for song in individual_songs:
        song = song['track']
        song_data[song['uri']] = {'artist' : song['artists'][0]['name'],
                                'album' : song['album']['name'],
                                'title' : song['name'],
                                'ablum_art' : song['album']['images'][0]['url'],
                                'track' : str(song['track_number'])}
        print( song['name'])

    for song in song_data:
        try:
            print ("")
            search_term = song_data[song]['artist'] + " " + song_data[song]['title'] + " lyrics"
            Search_URL = ''.join([i for i in filter(lambda x: x in set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c'), "https://www.youtube.com/results?search_query=" + '+'.join(search_term.replace("&", "%26").replace("=", "%3D").replace("*", "%3D").split(" ")))])

            print ("Getting " + Search_URL)
            
            driver = webdriver.Chrome() 
            driver.get(Search_URL)
            
            
            user_data = driver.find_elements_by_xpath('//*[@id="video-title"]')
            links = []
            for i in user_data:
                links.append(i.get_attribute('href'))

            print(len(links))
            for link in links:
                print(link)
                
                
            driver.close()    
  
            tileNum = 0
            for tile in links:
                tileNum+=1
                print("Trying tile # "+str(tileNum) )
                
                if ( tile == "None" ):
                    continue
                if ( tile == None ):
                    continue    
                video_URL = tile

# ffmpeg ffprobe fails on webm file type so we need to limit downloads to mp4 types
                fileListCwd = os.listdir(os.getcwd())
                print("Remove old mp3 files" )
                for i in fileListCwd:
                    if i.endswith(".mp3"):
                        os.remove(os.getcwd() + "\\" + i)
                    if i.endswith(".webm"):
                        os.remove(os.getcwd() + "\\" + i)
                print("Try the download link")
                for i in range(3):
                    # this fails sometimes so we try 3 times 
                    a = downloadYoutubeToMP3(video_URL)
                    if not a:
                        print ("Video download attempt " + str(i + 1) + " failed")
                    else:
                        print("Got a valid download")
                        break
                if not a:
                    print ("Failed on: " + song_data[song]['artist'] + "  - " + song_data[song]['title'])
                    continue
                else:
                    print("Got a valid download Break from tile loop")
                    break
           
            print ("Youtube Download Complete")
            fileListCwd = os.listdir(os.getcwd())
            for i in fileListCwd:
                if i.endswith(".mp3"):
                    file = os.getcwd() + "\\" + i
            try:
                print ("Tagging \\" + file.split("\\")[-1])
            except:
                print ("Tagging Failed")

            audio = MP3(file, ID3=ID3)
            try:
                audio.add_tags()
            except error:
                pass
            urllib.request.urlretrieve(song_data[song]['ablum_art'], (os.getcwd() + "/tempAlbumArt.jpg"))
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'cover', data=open(os.getcwd() + "/tempAlbumArt.jpg", 'rb').read()))
            audio.save()
            os.remove(os.getcwd() + "/tempAlbumArt.jpg")
            audio = EasyID3(file)
            audio["tracknumber"] = song_data[song]['track']
            audio["title"] = song_data[song]['title']
            audio["album"] = song_data[song]['album']
            audio["artist"] = song_data[song]['artist']
            audio.save()

            if not os.path.exists(outputDir):
                os.makedirs(outputDir)
            title = cleanString(song_data[song]['title'])
            artist = cleanString(song_data[song]['artist'])
            album = cleanString(song_data[song]['album'])

            try:

                passName[saveNum] = cleanString(artist + " - " + title + ".mp3")
                os.rename(file, (outputDir + passName[saveNum]))
                print ("Saved at: " + outputDir  + passName[saveNum])
            except Exception as e:
                print ("Could not rename to "+passName[saveNum] )
                print (repr(e))
                for i in range(10):
                    try:
                        newName = cleanString(artist + " - " + title + "(" + str(i+1) + ").mp3")
                        print ("Attempting: " + outputDir + newName )
                        os.rename(file, outputDir + newName )
                        passName[saveNum] = newName
                        print ("Saved at: " + outputDir + newName )
                        break
                    except Exception as ex:
                        print ("Rename Error on " + str(i) + ": " + str(repr(ex)))
        except Exception as e:
            print("Global Error Catcher")
            print (e)
            a = input("Figure out the problem")
        
        saveNum += 1


    print("Complete")

    return render_template(
        "playlist.html",
        name=name,
        date=datetime.now(),
        song1=passName[0],
        song2=passName[1],
        song3=passName[2],
        song4=passName[3],
        song5=passName[4],
        song6=passName[5],
        song7=passName[6],
        song8=passName[7],
        song9=passName[8],
        song10=passName[9]
        )


# flask tutorial
# Replace the existing home function with the one below
@app.route("/")
def home():
    return render_template("home.html")
	
	
@app.route("/MyList/")
def myList():
	 return render_template("mylist.html")

# New functions
@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/contact/")
def contact():
    return render_template("contact.html")

