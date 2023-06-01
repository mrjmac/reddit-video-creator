from pytube import YouTube
import os
from moviepy.editor import *
from random import randrange
import praw
from gtts import gTTS
from mutagen.mp3 import MP3
import json


try:
    import gizeh as gz
    GIZEH_AVAILABLE = True
except ImportError:
    GIZEH_AVAILABLE = False
import numpy as np
from moviepy.editor import ImageClip

def autocrop(np_img):
    """Return the numpy image without empty margins."""
    if len(np_img.shape) == 3:
        if np_img.shape[2] == 4:
            thresholded_img = np_img[:,:,3] # use the mask
        else:
            thresholded_img = np_img.max(axis=2) # black margins
    zone_x = thresholded_img.max(axis=0).nonzero()[0]
    xmin, xmax = zone_x[0], zone_x[-1]
    zone_y = thresholded_img.max(axis=1).nonzero()[0]
    ymin, ymax = zone_y[0], zone_y[-1]
    return np_img[ymin:ymax+1, xmin:xmax+1]

def text_clip(text, font_family, align='left',
              font_weight='normal', font_slant='normal',
              font_height = 70, font_width = None,
              interline= None, fill_color=(0,0,0),
              stroke_color=(0, 0, 0), stroke_width=2,
              bg_color=None):
    """Return an ImageClip displaying a text.
    
    Parameters
    ----------
    
    text
      Any text, possibly multiline
    
    font_family
      For instance 'Impact', 'Courier', whatever is installed
      on your machine.
    
    align
      Text alignment, either 'left', 'center', or 'right'.
      
    font_weight
      Either 'normal' or 'bold'.
    
    font_slant
      Either 'normal' or 'oblique'.
    
    font_height
      Eight of the font in pixels.
      
    font_width
      Maximal width of a character. This is only used to
      create a surface large enough for the text. By
      default it is equal to font_height. Increase this value
      if your text appears cropped horizontally.
    
    interline
      number of pixels between two lines. By default it will be
    
    stroke_width
      Width of the letters' stroke in pixels.
      
    stroke_color
      For instance (0,0,0) for black stroke or (255,255,255)
      for white.
    
    fill_color=(0,0,0),
      For instance (0,0,0) for black letters or (255,255,255)
      for white.
    
    bg_color
      The background color in RGB or RGBA, e.g. (255,100,230)
      (255,100,230, 128) for semi-transparent. If left to none,
      the background is fully transparent
    
    """
    
    if not GIZEH_AVAILABLE:
        raise ImportError("`text_clip` requires Gizeh installed.")

    stroke_color = np.array(stroke_color)/255.0
    fill_color = np.array(fill_color)/255.0
    if bg_color is not None:
        np.array(bg_color)/255.0

    if font_width is None:
        font_width = font_height
    if interline is None:
        interline = 0.3 * font_height
    line_height = font_height + interline
    lines = text.splitlines()
    max_line = max(len(l) for l in lines)
    W = int(max_line * font_width + 2 * stroke_width)
    H = int(len(lines) * line_height + 2 * stroke_width)
    surface = gz.Surface(width=W, height=H, bg_color=bg_color)
    xpoint = {
        'center': W/2,
        'left': stroke_width + 1,
        'right': W - stroke_width - 1
    }[align]
    for i, line in enumerate(lines):
        ypoint = (i+1) * line_height
        text_element = gz.text(line, fontfamily=font_family, fontsize=font_height,
                               h_align=align, v_align='top',
                               xy=[xpoint, ypoint], fontslant=font_slant,
                               stroke=stroke_color, stroke_width=stroke_width,
                               fill=fill_color)
        text_element.draw(surface)
    cropped_img = autocrop(surface.get_npimage(transparent=True))
    return ImageClip(cropped_img)


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
text = [title]
submission = reddit.submission(id)
i = 0
j = 0
size = 0

while (size < 250) :

    if (len(submission.comments[i].body) + size < 425) :

        text.append(submission.comments[i].body.replace(".", ","))
        size += len(text[j])
        j += 1

    i += 1


captions = []

for comment in text :

    formatted = ""
    rn_len = 0
    full = comment.split()

    for w in full :
        if rn_len + len(w) > 20 :
            formatted = formatted[:-1] + "\n"
            rn_len = 0

        formatted += w + " "
        rn_len += len(w)

    formatted = formatted[:-1] + "\n"
    temp = formatted.split("\n")
    temp.pop()
    captions.append(temp)

print(captions)

print("Comments found!")

# generate tts of the captions
i = 0
for array in captions :
    for comment in array :
        gTTS(text = comment, lang = language, slow = False).save("caption" + str(i) + ".mp3")
        i += 1

# generate tts of the comments
i = 0
for comment in text :
    gTTS(text = comment, lang = language, slow = False).save("comment" + str(i) + ".mp3")
    i += 1

# turn the captions into mp3s
caption = []
i = 0
for array in captions :
    curr = []
    for thing in array :
        curr.append(MP3("caption" + str(i) + ".mp3"))
        i += 1
    caption.append(curr)

# turn the comments into mp3s
comment = []
for i in range(len(text)) :
    comment.append(MP3("comment" + str(i) + ".mp3"))

caplength = []
total = 0

for array in caption :
    for thing in array :
        caplength.append(thing.info.length)

length = []
total = 0
for x in comment :
    length.append(x.info.length)
    total += x.info.length + 2

print("TTS generated!")

# record the total video time
time = round(total + 5)
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

curr = 0
commentaudio = []
for i in range(len(text)) :
    commentaudio.append(AudioFileClip("comment" + str(i) + ".mp3").set_start(curr))
    curr += length[i] + 2

i = 0
curr = 0
textclips = []
for array in captions :
    for thing in array :
        curr_text_clip = text_clip(thing, font_height = 110, fill_color = (255, 255, 255), stroke_color = (0, 0, 0), font_family = 'Sans', stroke_width = 1, align = 'center').set_start(curr).set_duration(caplength[i]).set_position((0, 540))
        textclips.append(curr_text_clip)
        curr += caplength[i]
        i += 1
    curr += 2


# combine the audioclips
finalaudio = commentaudio[0]
for i in range(len(text) - 1) :
   finalaudio = CompositeAudioClip([finalaudio, commentaudio[i + 1]])

print("Audio generated!")

i = 0
for array in captions :
    for thing in array :
        final = CompositeVideoClip([final, textclips[i]])
        i += 1

# set the video audio to the final audio file
final.audio = finalaudio
# write the video
final.set_duration(time)
final.write_videofile("final.mp4")

for i in range(len(text)) :
    os.remove("comment" + str(i) + ".mp3")

i = 0
for array in captions :
    for thing in array :
        os.remove("caption" + str(i) + ".mp3")
        i += 1

print("Video finished!")
