import asyncio
import discord
from discord.ext import commands
import json
import os.path
import _pickle
from twitch import TwitchClient


DISCORD_CLIENT = commands.Bot(command_prefix='!', description = "Follow twitch streamers and get notified when they go live!")

# Loads in twitch and discord keys from file.
if os.path.isfile('keys.json'):
    with open('keys.json', 'r') as file_handle:
        KEY = json.load(file_handle)

TWITCH_CLIENT = TwitchClient(client_id=KEY['twitch'])

CHANNEL_ID ='261104162656354306'

STREAMERS = {}


# Load STREAMERS from file.
if os.path.isfile('streamers.pkl'):
    with open('streamers.pkl', 'rb') as file_handle:
        STREAMERS = _pickle.load(file_handle)

@DISCORD_CLIENT.command(pass_context=True)
async def follow(context):
    """Follow a streamer on twitch.tv."""
    channel = context.message.channel
    streamer = context.message.content.replace("!follow ", "").lower()
    follower = context.message.author.id

    # Check twitch to see if streamer exists.
    if TWITCH_CLIENT.users.translate_usernames_to_ids(streamer) == []:
        await DISCORD_CLIENT.send_message(channel, "Failed to follow " + streamer + ". Channel does not exist.")
        return

    # Creates streamer object if it doesn't already exist.
    if not streamer in STREAMERS.keys():
        STREAMERS[streamer] = {'followers': [], 'live_status': False, 'message_id': None}

    # Assigns follower to streamer if they are not already following.
    if not follower in STREAMERS[streamer]['followers']:
        STREAMERS[streamer]['followers'].append(follower)
        await DISCORD_CLIENT.send_message(channel, "Following" + " " + streamer)
        print(STREAMERS)
    else:
        await DISCORD_CLIENT.send_message(channel, "Already following" + " " + streamer)

    # Save STREAMERS to file.
    with open('streamers.pkl', 'wb') as file_handle:
        _pickle.dump(STREAMERS, file_handle)


@DISCORD_CLIENT.command(pass_context=True)
async def unfollow(context):
    """Unfollow a streamer on twitch.tv."""
    channel = context.message.channel
    follower = context.message.author.id
    streamer = context.message.content.replace("!unfollow ", "").lower()

    # Check twitch to see if streamer exists.
    if TWITCH_CLIENT.users.translate_usernames_to_ids(streamer) == []:
        await DISCORD_CLIENT.send_message(channel, "Failed to unfollow " + streamer + ". Channel does not exist.")
        return

    # Unassign follower from streamer and removes streamer from dictionary if it has no followers left.
    if streamer in STREAMERS and follower in STREAMERS[streamer]['followers']:
        STREAMERS[streamer]['followers'].remove(follower)
        await DISCORD_CLIENT.send_message(channel, "Unfollowed" + " " + streamer)
        if STREAMERS[streamer]['followers'] == []:
            STREAMERS.pop(streamer)
        print(STREAMERS)
    else:
        await DISCORD_CLIENT.send_message(channel, "You are not following" + " " + streamer)

    # Save STREAMERS to file.
    with open('streamers.pkl', 'wb') as file_handle:
        _pickle.dump(STREAMERS, file_handle)


@DISCORD_CLIENT.command(pass_context=True)
async def following(context):
    """Check which streamers you are currently following."""
    channel = context.message.channel
    follower = context.message.author.id
    followed_streamers = []
    for streamer in STREAMERS:
        if follower in STREAMERS[streamer]['followers']:
            followed_streamers.append(streamer)
    if not followed_streamers == []:
        await DISCORD_CLIENT.send_message(channel, "You are following" + " " + ", ".join(followed_streamers))
    else:
        await DISCORD_CLIENT.send_message(channel, "You are not following any streamers")


async def generate_message():
    """Generates message when a streamer comes online."""
    await DISCORD_CLIENT.wait_until_ready()
    while not DISCORD_CLIENT.is_closed:
        print(STREAMERS)
        try:
            for streamer in STREAMERS.keys():
                previous_live_status = STREAMERS[streamer]['live_status']
                refresh_live_status(streamer)
                mentions = get_mentions(streamer)

                # Send message.
                if STREAMERS[streamer]['message_id'] == None:
                    if previous_live_status == False and STREAMERS[streamer]['live_status'] == True:
                        message = await DISCORD_CLIENT.send_message(discord.Object(id=CHANNEL_ID),", ".join(mentions) + " " + streamer + " is streaming http://twitch.tv/"+streamer)
                        STREAMERS[streamer]['message_id'] = message
                    with open('streamers.pkl', 'wb') as file_handle:
                        _pickle.dump(STREAMERS, file_handle)

                # Edit messages when streamer goes offline.
                if previous_live_status == True and STREAMERS[streamer]['live_status'] == False:
                    await DISCORD_CLIENT.edit_message(STREAMERS[streamer]['message_id'],", ".join(mentions) + " " + streamer + " has stopped streaming")
                    STREAMERS[streamer]['message_id'] = None
                    with open('streamers.pkl', 'wb') as file_handle:
                        _pickle.dump(STREAMERS, file_handle)
                await asyncio.sleep(0.1)
            await asyncio.sleep(10)
        except:
            continue




def get_mentions(streamer):
    """Returns list of followers for a streamer."""
    mentions = []
    for follower in STREAMERS[streamer]['followers']:
        mentions.append(discord.User(id=follower).mention)
    return mentions


def refresh_live_status(streamer):
    """Updates live status of a streamer."""
    try:
        streamer_id = TWITCH_CLIENT.users.translate_usernames_to_ids(streamer)[0]['id']
        if not TWITCH_CLIENT.streams.get_stream_by_user(streamer_id) == None:
            STREAMERS[streamer]['live_status'] = True
        else:
            STREAMERS[streamer]['live_status'] = False
    except:
        STREAMERS[streamer]['live_status'] = None

DISCORD_CLIENT.loop.create_task(generate_message())

DISCORD_CLIENT.run(KEY['discord'])


