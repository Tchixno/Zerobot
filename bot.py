# ======================================
# 💀 GOD TIER DISCORD BOT (FULL MAX)
# ======================================

import discord
from discord.ext import commands
from discord import app_commands
import json, os, random
from datetime import datetime, timedelta
from openai import OpenAI

import os

TOKEN = os.getenv("TOKEN")
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
ai = OpenAI(api_key=OPENAI_API_KEY)

FILES = {
    "users": "users.json",
    "config": "config.json",
    "shop": "shop.json",
    "missions": "missions.json"
}

def load(f):
    if not os.path.exists(FILES[f]): return {}
    return json.load(open(FILES[f]))

def save(f,d):
    json.dump(d, open(FILES[f],"w"), indent=4)

users, config, shop, missions = load("users"), load("config"), load("shop"), load("missions")

config.setdefault("currency","Coins")
config.setdefault("xp",10)
config.setdefault("xp_needed",100)

def user(uid):
    uid=str(uid)
    if uid not in users:
        users[uid]={"money":0,"bank":0,"xp":0,"level":1,"inventory":[],"daily":"","weekly":""}
    return users[uid]

@bot.event
async def on_ready():
    await tree.sync()
    print("READY")

@bot.event
async def on_message(m):
    if m.author.bot: return
    u=user(m.author.id)
    u["xp"]+=config["xp"]
    if u["xp"]>=config["xp_needed"]:
        u["xp"]=0
        u["level"]+=1
        await m.channel.send(f"🎉 {m.author.mention} LEVEL {u['level']}")
    save("users",users)
    await bot.process_commands(m)

# ================= ECONOMY =================

class Economy(app_commands.Group):
    def __init__(self):
        super().__init__(name="economy", description="Money system")

    @app_commands.command()
    async def balance(self,i:discord.Interaction):
        u=user(i.user.id)
        await i.response.send_message(f"💰 {u['money']} | 🏦 {u['bank']}")

    @app_commands.command()
    async def work(self,i:discord.Interaction):
        u=user(i.user.id)
        g=random.randint(50,150)
        u["money"]+=g
        save("users",users)
        await i.response.send_message(f"💼 +{g}")

    @app_commands.command()
    async def daily(self,i:discord.Interaction):
        u=user(i.user.id)
        now=datetime.now()
        if u["daily"] and now-datetime.fromisoformat(u["daily"])<timedelta(hours=24):
            return await i.response.send_message("⏳ cooldown")
        g=random.randint(200,400)
        u["money"]+=g
        u["daily"]=now.isoformat()
        save("users",users)
        await i.response.send_message(f"🎁 {g}")

    @app_commands.command()
    async def deposit(self,i:discord.Interaction,amount:int):
        u=user(i.user.id)
        if amount>u["money"]: return await i.response.send_message("❌")
        u["money"]-=amount;u["bank"]+=amount
        save("users",users)
        await i.response.send_message("🏦 done")

    @app_commands.command()
    async def withdraw(self,i:discord.Interaction,amount:int):
        u=user(i.user.id)
        if amount>u["bank"]: return await i.response.send_message("❌")
        u["bank"]-=amount;u["money"]+=amount
        save("users",users)
        await i.response.send_message("💵 done")

    @app_commands.command()
    async def leaderboard(self,i:discord.Interaction):
        top=sorted(users.items(),key=lambda x:x[1]["money"],reverse=True)[:10]
        txt="🏆 Leaderboard:\n"
        for k,v in top:
            txt+=f"<@{k}> - {v['money']}\n"
        await i.response.send_message(txt)

tree.add_command(Economy())

# ================= CASINO =================

@tree.command()
async def coinflip(i:discord.Interaction,bet:int):
    u=user(i.user.id)
    if bet>u["money"]: return await i.response.send_message("❌")
    if random.random()<0.5:
        u["money"]+=bet
        msg=f"🪙 WIN +{bet}"
    else:
        u["money"]-=bet
        msg=f"💀 LOST {bet}"
    save("users",users)
    await i.response.send_message(msg)

@tree.command()
async def slots(i:discord.Interaction,bet:int):
    u=user(i.user.id)
    if bet>u["money"]: return await i.response.send_message("❌")
    s=["🍒","💎","🔥"]
    r=[random.choice(s) for _ in range(3)]
    if len(set(r))==1:
        win=bet*3
        u["money"]+=win
        msg=f"{r} JACKPOT {win}"
    else:
        u["money"]-=bet
        msg=f"{r} lost"
    save("users",users)
    await i.response.send_message(msg)

# ================= SHOP =================

@tree.command()
async def shop_cmd(i:discord.Interaction):
    msg="🛒\n"
    for k,v in shop.items():
        msg+=f"{k}:{v['price']}\n"
    await i.response.send_message(msg)

@tree.command()
async def buy(i:discord.Interaction,item:str):
    u=user(i.user.id)
    if item not in shop: return await i.response.send_message("❌")
    if u["money"]<shop[item]["price"]: return await i.response.send_message("❌")
    u["money"]-=shop[item]["price"]
    u["inventory"].append(item)
    save("users",users)
    await i.response.send_message("✅ bought")

# ================= MISSIONS =================

@tree.command()
async def missions_cmd(i:discord.Interaction):
    msg="🎯\n"
    for k,v in missions.items():
        msg+=f"{k}:{v['reward']}\n"
    await i.response.send_message(msg)

# ================= AI =================

@tree.command()
async def ai_cmd(i:discord.Interaction,prompt:str):
    r=ai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"user","content":prompt}]
    )
    await i.response.send_message(r.choices[0].message.content[:2000])

# ================= CONFIG =================

class Config(app_commands.Group):
    def __init__(self):
        super().__init__(name="config", description="Admin config")

    @app_commands.command()
    async def currency(self,i:discord.Interaction,name:str):
        if not i.user.guild_permissions.administrator: return
        config["currency"]=name
        save("config",config)
        await i.response.send_message("✅")

    @app_commands.command()
    async def add_shop(self,i:discord.Interaction,name:str,price:int):
        if not i.user.guild_permissions.administrator: return
        shop[name]={"price":price}
        save("shop",shop)
        await i.response.send_message("✅")

    @app_commands.command()
    async def add_mission(self,i:discord.Interaction,name:str,reward:int):
        if not i.user.guild_permissions.administrator: return
        missions[name]={"reward":reward}
        save("missions",missions)
        await i.response.send_message("✅")

tree.add_command(Config())

bot.run(TOKEN)

import os

TOKEN = os.getenv("TOKEN")

bot.run(TOKEN)