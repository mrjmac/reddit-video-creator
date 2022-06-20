# Reddit-Video-Creator
Automatically creates a video which reads out comments in a reddit thread overbackground gameplay, just like you'd see in youtube shorts or on tiktok

This isn't actively being worked on, however the biggest improvement to be made is to automatically find a series of comments that would make the video 30 seconds long

Here's how it works:

1. Find one of the top 10 current posts on hot in AskReddit
2. Using DOM elements, takes a screenshot of the post title and top comment
3. Generate text to speech for the comment and title
4. Download minecraft gameplay and cut to a random part
5. Process everything together using moviepy

# Imporant Info
It uses python3 and was tested on ubuntu.

It takes about 30 seconds to generate a video, however this all depends on comment length

All necessary libraries are listed at the top imports
