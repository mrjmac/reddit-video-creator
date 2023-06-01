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
text = [[title, id, url]]
submission = reddit.submission(id)
i = 0
j = 0
size = 0

while (size < 250 and len(text) < 4) :

    if (len(submission.comments[i].body) + size < 350) :

        text.append([submission.comments[i].body.replace(".", ","), submission.comments[i].id, "http://www.reddit.com" + submission.comments[i].permalink])
        size += len(text[j][0])
        j += 1

    i += 1

print("Comments found!")

# screenshot the post title and the top comment
with sync_playwright() as p:

    # launch browser
    browser= p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.reddit.com/login")
    page.wait_for_load_state()

    page.locator('[name="username"]').fill(username)
    page.locator('[name="password"]').fill(password)
    page.locator("button[class$='m-full-width']").click()
    page.wait_for_timeout(5000)
    page.wait_for_load_state()

    i = 0
    for content in text :
        # navigate to the reddit post and set the screen size
        page.goto(content[2])
        page.wait_for_load_state()
        page.set_viewport_size(ViewportSize(width = 1920, height = 1080))

        # navigate past NSFW warning if applicable
        if page.locator('[class="px-md button-medium px-[length:var(--rem14)] button-secondary   button inline-flex justify-center"]').is_visible():
                page.locator('[class="px-md button-medium px-[length:var(--rem14)] button-secondary   button inline-flex justify-center"]').click()

        # screenshot the content using DOM navigation
        if (i == 0) :
            page.locator("#t3_" + content[1]).screenshot(path="screenshot0.png")
        if (i != 0) :
            page.locator("#t1_" + content[1]).screenshot(path="screenshot" + str(i) + ".png")

        i += 1

print("Screenshots taken!")

# generate tts of the content
i = 0
for content in text :
    gTTS(text = content[0], lang = language, slow = False).save("content" + str(i) + ".mp3")
    i += 1

# turn the tts into an mp3 file
contentmp3 = []
for i in range(len(text)) :
    contentmp3.append(MP3("content" + str(i) + ".mp3"))

# record the total video time
length = []
total = 0
for x in contentmp3 :
    length.append(x.info.length)
    total += x.info.length + 2

time = round(total + 3)

# convert our mp3s into audiofileclips
curr = 0
audiofileclips = []
imageclips = []

for i in range(len(text)) :
    audiofileclips.append(AudioFileClip("content" + str(i) + ".mp3").set_start(curr))
    imageclips.append(ImageClip("screenshot" + str(i) + ".png").set_start(curr).set_position("center").resize(width = 980).set_duration(contentmp3[i].info.length))
    curr += length[i] + 2

# combine the audioclips
finalaudio = audiofileclips[0]
for i in range(len(text) - 1) :
   finalaudio = CompositeAudioClip([finalaudio, audiofileclips[i + 1]])

# delete the mp3s
for i in range(len(text)) :
    os.remove("content" + str(i) + ".mp3")

print("Audio generated!")

# download the minecraft parkour video we want to use
if not os.path.exists("parkour.mp4") :
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

for i in range(len(text)) :
   final = CompositeVideoClip([final, imageclips[i]])

# delete the mp3s
for i in range(len(text)) :
    os.remove("screenshot" + str(i) + ".png")

# set the video audio to the final audio file
final.audio = finalaudio

# write the video
final.write_videofile("final.mp4")

print("Video finished!")