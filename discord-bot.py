#!/usr/bin/env python3

import asyncio
import youtube_dl
import os

import discord
import bs4
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


#####

def ping(user):
    return f'<@{user.id}>'

async def move_user_to_voice_channel(user, channel):
    if user.voice == None:
        return
    if user.voice.channel == channel:
        return
    
    try:
        await user.move_to(channel)
    except discord.errors.HTTPException:
        return

#####

MEDIA_FOLDER = './media/'

async def search_odysee_for_videos(search_for):
    BASE_URL = 'https://odysee.com/'
    SEARCH_URL = BASE_URL + '$/search?q={}'
    #
    TIME_TO_LOAD_PAGE = 16

    dir_ = MEDIA_FOLDER + search_for
    if os.path.isfile(dir_):
        return [dir_]

    url = SEARCH_URL.format(search_for)

    options = Options()
    options.headless = True
    with webdriver.Firefox(options=options) as driver:
        driver.get(url)
        await asyncio.sleep(0)

        try:
            WebDriverWait(driver, TIME_TO_LOAD_PAGE).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div[1]/main/section/section/ul/li[1]/div/div/div[1]/div[1]/a/div/span')))
        except TimeoutException:
            return []

        videos = driver.find_elements_by_xpath("//a[@href]")
        video_links = []
        for video in videos:
            full_link = video.get_attribute('href')
            link = full_link

            if not link.startswith(BASE_URL):
                continue
            link = link[len(BASE_URL):]

            if not link.startswith('@'):
                continue
            link = link[1:]

            if '/' not in link:
                continue

            link = full_link
            if link not in video_links:
                video_links.append(link)

            await asyncio.sleep(0)

    return video_links

async def play_video_from_link(vc, video_link):
    if os.path.isfile(video_link):
        source = discord.FFmpegPCMAudio(video_link)
        
    else:
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        }
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        video_data = ytdl.extract_info(video_link, download=False)

        ffmpeg_options = {
            'options': '-vn'
        }
        url = video_data['url']
        print(f'now playing music from URL: {url}')
        source = discord.FFmpegPCMAudio(url, **ffmpeg_options)

    vc.play(source)

    while vc.is_playing():
        await asyncio.sleep(1)

#####

async def handle_music_related_activities(msg):
    PLAY_PHRASE = 'pusni mi '
    SEARCH_PHRASE = 'tursi '

    content = msg.content
    
    if content.startswith(PLAY_PHRASE):
        voice = msg.author.voice
        if voice == None:
            await msg.channel.send(ping(msg.author) + ' is a nigger')
            return
        
        search_for = content[len(PLAY_PHRASE):]

        await msg.channel.send(f'trying to play {search_for}')
        search_results = await search_odysee_for_videos(search_for)
        
        if len(search_results) == 0:
            await msg.channel.send(f'no results found / page timed out: {search_for}')
            return
        link = search_results[0]

        try:
            vc = await voice.channel.connect()
        except discord.errors.ClientException:
            await msg.channel.send('im already playing')
            return
        
        try:
            await msg.channel.send(f'Now playing: {link}')
            await play_video_from_link(vc, link)
        finally:
            await vc.disconnect()
        
    elif content.startswith(SEARCH_PHRASE):
        search_for = content[len(SEARCH_PHRASE):]
        await msg.channel.send(f'searching for {search_for}')
        search_results = await search_odysee_for_videos(search_for)
        res = f'Results for {search_for}:\n'
        res += '\n'.join(search_results)
        await msg.channel.send(res)


    
class Event_hunter(discord.Client):
    def __init__(s):
        super().__init__()
        s.real_servers = []
        s.real_server_handlers = []
    def real_get_server(s, server):
        if server in s.real_servers:
            return s.real_server_handlers[s.real_servers.index(server)]

        handler = Server_handler()
        s.real_servers.append(server)
        s.real_server_handlers.append(handler)
        return handler

    async def on_ready(s):
        print(f'Logged in as: {s.user}')

    async def on_voice_state_update(s, member, state_before, state_after):
        if member == s.user:
            return
        server = member.guild
        handle = s.real_get_server(server)
        
        await handle.on_voice_update(member, state_before, state_after)

    async def on_message(s, msg):
        if msg.author == s.user:
            return
        server = msg.guild
        handle = s.real_get_server(server)
        
        await handle.on_message(msg)


class Server_handler:
    def __init__(s):
        s.actors = [Sus_detector(), Music_bot()]

    async def call_actors(s, event, a, kw):
        for actor in s.actors:
            if event in dir(actor):
                fnc = eval(f'actor.{event}')
                await fnc(*a, **kw)

    async def on_voice_update(s, *a, **kw):
        await s.call_actors('on_voice_update', a, kw)

    async def on_message(s, *a, **kw):
        await s.call_actors('on_message', a, kw)
                

class Sus_detector:
    def __init__(s):
        s.emergency_meeting_in_progress = False
        s.emergency_room = None
        
    async def on_voice_update(s, member, before, after):
        if s.emergency_meeting_in_progress:
            await move_user_to_voice_channel(member, s.emergency_room)

    async def on_message(s, msg):
        
        content = msg.content
        content_lower = content.lower()

        for sus in ['sus', 'сус', 'със']:

            if sus in content_lower:
                ind = content_lower.index(sus)
                sus = content[ind:ind+len(sus)]

                # msg reaction
                for emoji in ['🇸', '🇺', '5️⃣']:
                    await msg.add_reaction(emoji)

                # respond to his msg
                await msg.reply(ping(msg.author) + f' acting kinds of {sus}')

                # check if the audio file exists
                audio_source = discord.FFmpegPCMAudio('when the imposter is sus.mp4')

                # check if user is in voice
                voice = msg.author.voice
                if voice == None:
                    await msg.channel.send(ping(msg.author) + ' not in voice')
                    return
                emergency_room = voice.channel

                # check if we're already doing smt in voice
                try:
                    vc = await emergency_room.connect()
                except discord.errors.ClientException:
                    await msg.channel.send('already connected to voice')
                    return

                # see who needs to attend
                meeting_members = []
                for vc_ in msg.guild.voice_channels:
                    for member in vc_.members:
                        meeting_members.append(member)

                # alert the attendees
                info = ''
                for member in meeting_members:
                    info += ping(member) + ' '
                info += 'emergency meeting'

                #
                s.emergency_room = emergency_room
                s.emergency_meeting_in_progress = True
                try:
                    
                    # call them into the room
                    for member in meeting_members:
                        await move_user_to_voice_channel(member, emergency_room)

                    # talk
                    vc.play(audio_source)

                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await vc.disconnect()

                finally:
                    s.emergency_meeting_in_progress = False

                return



class Music_bot:
    async def on_message(s, msg):
        await handle_music_related_activities(msg)
    


shell = Event_hunter()

#client.run('ODQ1Mzk3MzgwMDUxMzcwMDQ1.YKgX9A.2WyhdJnRmdgxhdi9lgcRtoTQ-nU', bot=False)
shell.run('ODQ1NDAzNTg4NTkxMzUzOTI2.YKgdcg._dPAZURSxLBfMYpPc0Zyfn4pTUg')

