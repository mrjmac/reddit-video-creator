from pytube import YouTube
import os
from moviepy.editor import *
from random import randrange
import praw
from playwright.sync_api import sync_playwright, ViewportSize
from gtts import gTTS
from mutagen.mp3 import MP3
import json

with open("config.json", "r") as f:
    my_dict = json.load(f)

# login info
client_id = my_dict["client_id"]
client_secret = my_dict["client_secret"]
username = my_dict["username"]
password = my_dict["password"]
user_agent = my_dict["user_agent"]

# initalize tts
language = 'en'

# login to reddit and navigate to askreddit
reddit = praw.Reddit(client_id = client_id, client_secret = client_secret, username = username, passkey = password, user_agent = user_agent, check_for_async=  False)
target_sub = "AskReddit"
subreddit = reddit.subreddit(target_sub)

print("Logging in to Reddit!")

# pick one of the top 10 posts on hot to make a video about, grab the post title, url, and id
randnum = randrange(0, 10)
i = 0
for submission in reddit.subreddit(target_sub).hot(limit = 10) :
    if i == randnum :
        title = submission.title
        id = submission.id
        url = submission.url
    i += 1

print("Post found!")

# grab the enough comments to make a decently long video
text = []
submission = reddit.submission(id)
i = 0
j = 0
size = 0

while (size < 300) :

    if (len(submission.comments[i].body) + size < 425) :

        text.append(submission.comments[i].body.replace(".", ","))
        size += len(text[j])
        j += 1

    i += 1

captions = []

formatted = ""
for comment in text :

    rn_len = 0
    full = comment.split()

    for w in full :
        if rn_len + len(w) > 40 :
            formatted = formatted[:-1] + "\n"
            rn_len = 0

        formatted += w + " "
        rn_len += len(w)

    formatted = formatted[:-1] + "\n"

captions = formatted.split("\n")
captions.pop()

print(captions)

print("Comments found!")

# generate tts of the title
gTTS(text = title, lang = language, slow = True).save("title.mp3")

# generate tts of the comments
i = 0
for comment in text :
    gTTS(text = comment, lang = language, slow = False).save("comment" + str(i) + ".mp3")
    i += 1

# turn the tts into an mp3 file
title = MP3("title.mp3")

comment = []
for i in range(len(text)) :
    comment.append(MP3("comment" + str(i) + ".mp3"))

length = [title.info.length]
total = 0
for x in comment :
    length.append(x.info.length)
    total += x.info.length + 2

print("TTS generated!")

# record the total video time
time = round(title.info.length + total + 5)
if not os.path.exists("parkour.mp4") :
    # download the minecraft parkour video we want to use
    url = 'https://www.youtube.com/watch?v=a5B8Xx1RPSc'
    yt = YouTube(url)

    mp4_files = yt.streams.filter(file_extension="mp4")
    mp4_720p_files = mp4_files.get_by_resolution("720p")
    mp4_720p_files.download(filename='parkour.mp4')

print("Parkour downloaded!")


# download the minecraft parkour video, strip the audio, and cut the video to a random point that lasts the length of the audio
background = VideoFileClip('parkour.mp4')
background = background.without_audio()
start_time = randrange(0, 450)
background = background.subclip(start_time, start_time + time)

# resize and crop the video to fit a mobile screen(1920x1080)
final = (
    background
    .resize(height = 1920)
    .crop(x1=1000, y1=0, x2=2080, y2=1920)
)

# convert our mp3s into audiofileclips
titleaudio = AudioFileClip("title.mp3")

curr = 0
commentaudio = []
for i in range(len(text)) :
    curr += length[i] + 2
    commentaudio.append(AudioFileClip("comment" + str(i) + ".mp3").set_start(curr))


# combine the audioclips
finalaudio = CompositeAudioClip([titleaudio, commentaudio[0]])
for i in range(len(text) - 1) :
   finalaudio = CompositeAudioClip([finalaudio, commentaudio[i + 1]])

print("Audio generated!")

#final = CompositeVideoClip([final, text_clip])

# set the video audio to the final audio file
final.audio = finalaudio
# write the video
final.write_videofile("final.mp4")

print("Video finished!")
