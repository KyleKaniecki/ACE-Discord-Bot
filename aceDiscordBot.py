#!/usr/bin/env python

import discord
import os
import datetime


class Cache(object):
    """
    Represents the internal cache list
    Stored as the following dictionary
    {
        <member_name>: [
            {
                "expiry": datetime Object,
                "action": 20 for remove, 22 for ban
            },
            ...
        ],
        ...
    }
    """

    cache = {}

    def add_cache_item(self, username: str, action: int):
        if username not in self.cache.keys():
            self.cache[username] = []

        self.cache[username].append({
            "expiry": datetime.datetime.now() + datetime.timedelta(minutes=5),
            "action": action
        })

    def get_user_actions(self, username: str, target: int = 20):
        return [action for action in self.cache.get(username) if action['action'] == target]

    def prune(self):
        # Iterate through all the cache items
        for username, actions in self.cache.items():
            # Iterate through all of the actions the user has performed and remove expired ones
            self.cache[username] = [action for action in actions if action['expiry'] > datetime.datetime.now()]


def kick_audit_predicate(event):
    return event.action == discord.AuditLogAction.kick

def ban_audit_predicate(event):
    return event.action == discord.AuditLogAction.ban


class ACEClient(discord.Client):

    channel_whitelist = [
        'general',
    ]

    cache = Cache()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        #self.bg_task = self.loop.create_task(self.my_background_task())
        self.send_block = False

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name='Straight Chillin\''))

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        log = await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).find(ban_audit_predicate)

        self.cache.prune()
        self.cache.add_cache_item(log.user.name, 22)
        recent_bans = self.cache.get_user_actions(log.user.name, 22)

        if len(recent_bans) >= 10:
            # Message Mateo about banning as a warning for this user
            owner = guild.owner
            await owner.send(
                "Ok, {} is banning too many people. "
                "I am gonna remove their top permission for now.".format(log.user.name)
            )
            await log.user.remove_roles(log.user.top_role)

        if len(recent_bans) == 3:
            # Remove user role that allows for bans
            owner = guild.owner
            await owner.send(
                "Yo, {} has banned 3 people in the last 5 minutes. "
                "You should probably check that out.".format(log.user.name)
            )


    async def on_member_remove(self, member: discord.Member):
        log = None
        for guild in self.guilds:
            log =  await guild.audit_logs(limit=5, action=discord.AuditLogAction.kick).find(kick_audit_predicate)
            if log:
                break

        if log:
            self.cache.prune()
            self.cache.add_cache_item(log.user.name, 20)
            recent_kicks = self.cache.get_user_actions(log.user.name, 20)

            if len(recent_kicks) >= 20:
                owner = log.guild.owner
                await owner.send(
                    "Ok, {} is kicking too many people. "
                    "I am gonna remove their top permission for now.".format(log.user.name)
                )
                await log.user.remove_roles(log.user.top_role)
            elif len(recent_kicks) == 10:
                owner = log.guild.owner
                await owner.send('Yo, {} is kicking a lot of people. You might wanna check that out'.format(log.user.name))


client = ACEClient()
client.run(os.environ.get('DISCORD_API_KEY', ''))

