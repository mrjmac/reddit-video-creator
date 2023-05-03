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

# pick one of the top 10 posts on hot to make a video about, grab the post title, url, and id
randnum = randrange(0, 10)
i = 0
for submission in reddit.subreddit(target_sub).hot(limit = 10) :
    if i == randnum :
        title = submission.title
        id = submission.id
        url = submission.url
    i += 1

# grab the top comment in the thread, save it's body, url, and id
submission = reddit.submission(id)
comment = submission.comments[0].body
comment_url = "http://www.reddit.com" + submission.comments[0].permalink
comment_id = submission.comments[0].id

"""
# screenshot the post title and the top comment
with sync_playwright() as p:

    # launch browser
    browser= p.chromium.launch()
    context = browser.new_context()

    # navigate to the reddit post and set the screen size
    page = context.new_page()
    page.goto(url)
    page.set_viewport_size(ViewportSize(width = 1920, height = 1080))

    # navigate past NSFW warning if applicable
    if page.locator('[data-testid="content-gate"]').is_visible():
            page.locator('[data-testid="content-gate"] button').click()

    # screenshot the title using DOM navigation
    page.locator('[data-test-id="post-content"]').screenshot(path="title.png")



    # navigate to the top comment and maintain the same screen size
    page.goto(comment_url)
    page.set_viewport_size(ViewportSize(width = 1920, height = 1080))
    
    # navigate past NSFW warning if applicable
    if page.locator('[data-testid="content-gate"]').is_visible():
            page.locator('[data-testid="content-gate"] button').click()

    # locate the div of the comment and screenshot 
    page.locator(f"#t1_{comment_id}").screenshot(path="comment.png")
"""
# generate tts of the comments
gTTS(text = comment, lang = language, slow = False).save("comment.mp3")
gTTS(text = title, lang = language, slow = True).save("title.mp3")

# turn the tts into an mp3 file
title = MP3("title.mp3")
comment = MP3("comment.mp3")

# record the total video time
time = round(title.info.length + comment.info.length + 5)

# download the minecraft parkour video we want to use
url = 'https://www.youtube.com/watch?v=a5B8Xx1RPSc'
yt = YouTube(url)


mp4_files = yt.streams.filter(file_extension="mp4")
mp4_720p_files = mp4_files.get_by_resolution("720p")
mp4_720p_files.download(filename='parkour.mp4')

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
commentaudio = AudioFileClip("comment.mp3").set_start(title.info.length + 2)

"""
# convert our sceenshots into imageclips, set their start times, positions, size, and durations
finalcomment = (
    ImageClip("comment.png")
    .set_start(title.info.length + 2)
    .set_position("center")
    .resize(width = 980)
    .set_duration(comment.info.length)
)

finaltitle = (
    ImageClip("title.png")
    .set_position("center")
    .resize(width = 980)
    .set_duration(title.info.length)
)
"""

# combine the audioclips
finalaudio = CompositeAudioClip([titleaudio, commentaudio])
"""
# combine the video clips
final = CompositeVideoClip([final, finaltitle, finalcomment])
"""
# set the video audio to the final audio file
final.audio = finalaudio
# write the video
final.write_videofile("final.mp4")





