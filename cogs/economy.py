import discord
from discord.ext import commands
import random
import aiosqlite
import time
import asyncio
class Economy(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command()
    @commands.is_owner()
    async def makefile(self,ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS economy (UserID INT, Money Float, Daily INT)")
            await db.commit()
            await db.execute("Drop TABLE IF EXISTS Baking")
            await db.execute("CREATE TABLE IF NOT EXISTS Baking (UserID INT, Amount_Baking,TimeIn INT,Timeout INT)")
            await db.commit()
            await ctx.send("file made oh lord")

    @commands.slash_command()
    async def bal(self,ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute("SELECT money FROM economy WHERE UserID = ?",(user.id,))
            data = await data.fetchone()
            if data is None:
                await db.execute("INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",(user.id, 0,0))
                await db.commit()
                await ctx.respond("You have no donuts")
            else:
                await ctx.respond(f"You have {round(data[0],2)} Donuts 🍩")


    @commands.slash_command()
    async def daily(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            user = ctx.author
            data = await db.execute("SELECT * FROM economy WHERE UserID = ?",(user.id,))
            data = await data.fetchone()
            if data is None:
               await db.execute("INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",(user.id, 5,time.time()))
               await db.commit()
               await ctx.respond("You have claimed your daily and now have 5 Donuts 🍩")
            else:
                if time.time() - data[2] >= 86400:
                    await db.execute("UPDATE economy SET Money = ?,daily =? WHERE UserID = ?",(data[1] + 5,time.time(), ctx.author.id))
                    await ctx.respond(f"You have claimed your daily and now have {data[1] + 5} 🍩")
                    await db.commit()
                else:
                    await ctx.respond(f"You have to wait {round(int(86400 - (time.time() - data[2]))/3600,2)} hours to claim your daily 🍩")



    @commands.slash_command()
    async def bal_top(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute("SELECT * FROM economy ORDER BY Money DESC LIMIT 10")
            data = await data.fetchall()
            embed = discord.Embed(title="Top 10 Donut Holders", color=0x00ff00)
            for i in range(len(data)):
                user = await self.client.fetch_user(data[i][0])
                embed.add_field(name=f"{i + 1}. {user}", value=f"{round(data[i][1],2)} Donuts 🍩", inline=False)
            await ctx.respond(embed=embed)


    @commands.slash_command()
    async def send(self, ctx, user: discord.Member, amount: int):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            userto = await db.execute("SELECT * FROM economy WHERE UserID = ?",(user.id,))
            userfrom = await db.execute("SELECT * FROM economy WHERE UserID = ?",(ctx.author.id,))
            userto = await userto.fetchone()
            userfrom = await userfrom.fetchone()
            if userto == userfrom:
                await ctx.respond("You cant send to your self")
                return
            if amount <= 0:
                await ctx.respond("You cant send a negative amount")
                return
            if userfrom[1] <= amount:
                await ctx.respond("You dont have enough money to send that")
                return
            await ctx.respond(f"Transaction protocol starting... ", ephemeral=True)
            msg = await ctx.channel.send(f"{ctx.author.mention} is about to give {user} {amount} Donuts 🍩. React with ✅ to confirm or ❌ to cancel.")
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, usercheck):
                return usercheck == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message == msg

            try:
                reaction, usercheck = await self.client.wait_for("reaction_add", timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await msg.edit(content="Confirmation timed out.")
                await msg.remove_reaction("✅", self.client.user)
                await msg.remove_reaction("❌", self.client.user)
                return

            if str(reaction.emoji) == "✅":
                await msg.edit(content=f"You have given {user} {amount} Donuts 🍩")
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?",(userto[1] + amount,user.id,))
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?",(userfrom[1] - amount,ctx.author.id,))
                await db.commit()
            else:
                await msg.edit(content="Transaction cancelled.")
            await msg.clear_reactions()

            #if data is None:
            #    await db.execute("INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",(user.id, amount,0))
            #    await db.commit()
            #    await ctx.respond(f"You have given {user} {amount} Donuts 🍩")
            #else:
            #    await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?",(data[1] + amount,user.id))
            #    await db.commit()
            #    await ctx.respond(f"You have given {user} {amount} Donuts 🍩")


    @commands.slash_command()
    async def rps(self, ctx, choice: str, amount: int):
        # gamble with rock paper scissors
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute("SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,))
            data = await data.fetchone()
            if data is None:
                await ctx.respond("You have no donuts")
            if amount <= 0:
                await ctx.respond("You can't bet a negative amount or nothing")
                return
            else:
                if data[1] < amount:
                    await ctx.respond("You don't have enough donuts")
                else:
                    choices = ["rock", "paper", "scissors"]
                    if choice not in choices:
                        await ctx.respond("Invalid choice. Please choose rock, paper, or scissors.")
                    else:
                        bot_choice = random.choice(choices)
                        result = None
                        if choice == bot_choice:
                            result = "tie"
                        elif (choice == "rock" and bot_choice == "scissors") or (choice == "paper" and bot_choice == "rock") or (choice == "scissors" and bot_choice == "paper"):
                            result = "win"
                        else:
                            result = "lose"

                        new_balance = data[1] - amount
                        if result == "win":
                            new_balance += int(amount * 1.5)
                        if result == "tie":
                            new_balance + amount

                        await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (new_balance, ctx.author.id,))
                        await db.commit()

                        if result == "tie":
                            await ctx.respond(f"Bot chose {bot_choice}. It's a tie!")
                        elif result == "win":
                            await ctx.respond(f"Bot chose {bot_choice}. You won {int(amount * 1.5)} donuts! Your new balance is {new_balance}.")
                        else:
                            await ctx.respond(f"Bot chose {bot_choice}. You lost {amount} donuts. Your new balance is {new_balance}.")


    @commands.slash_command()
    async def bake(self,ctx):
        async with aiosqlite.connect("datebases\donuts.db") as db:
            amount = 1
            amount = amount * 5
            money = await db.execute("SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,))
            money = await money.fetchone()
            


            Baking = await db.execute("SELECT * FROM Baking WHERE UserID = ?", (ctx.author.id,))
            Baking = await Baking.fetchone()
            mins = random.randint(30, 300)
            #if baking does not exist set userID, amount to 1, and timein to current time and time out to current time + 5 minutes
            if Baking is None:
                if money is None:
                    await db.execute("INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",(ctx.author.id, 0,0))
                    await db.commit()
                    await ctx.respond("You have no donuts")
                    return
                if money[1] < amount:
                    await ctx.respond("You don't have enough donuts")
                    return
            
                moneyset = money[1] - amount
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (moneyset, ctx.author.id,))
                await db.commit()
                await db.execute("INSERT OR IGNORE INTO Baking (UserID,Amount_Baking,timein,timeout)  VALUES (?, ?,?,?)",(ctx.author.id, amount,time.time(),time.time() + mins * 60))
                await db.commit()
                await ctx.respond(f"You have started baking {amount} donuts they will be done in {mins} minutes")
                return
            #if there is food in the oven and the time to take out is plus or minus from 2 minutes of the current time give the user 1.5x the amount of donuts then remove the collum from the database 
            if Baking[3] < time.time() + 120 and Baking[3] > time.time() - 120:
                amountgiving = Baking[1] * 1.25
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (money[1] + amountgiving, ctx.author.id,))
                await db.execute("DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,))
                await db.commit()
                await ctx.respond(f"You have finished baking {amount * 1.5} donuts")
                return
            if Baking[3] < time.time() + 350 and Baking[3] > time.time() - 350:
                amountgiving = Baking[1] * 1.1
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (money[1] + amountgiving, ctx.author.id,))
                await db.execute("DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,))
                await db.commit()
                await ctx.respond(f"You have finished baking but you just missed the perfect moment. You made {amount * 1.2} donuts")
                return
            #if the food is taken out to soon give the user nothing and remove the collum from the database. Tell them they took it out to soon
            if Baking[3] > time.time():
                await db.execute("DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,))
                await db.commit()
                await ctx.respond(f"You took out your food to soon and it raw. You made no donuts")
                return
            #if the food is taken out to late give the user nothing and remove the collum from the database. Tell them they took it out to soon
            if Baking[3] < time.time():
                await db.execute("DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,))
                await db.commit()
                await ctx.respond(f"You took out your food to late and it burnt. You made no donuts")
                return
            
            


            


    @commands.command()
    @commands.is_owner()
    async def force_add(self,ctx, user: discord.Member, amount: int):
        async with aiosqlite.connect("datebases\donuts.db") as db:
            data = await db.execute("SELECT * FROM economy WHERE UserID = ?", (user.id,))
            data = await data.fetchone()
            await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (amount, user.id,))
            await db.commit()
            await ctx.send("done")


def setup(client):
    client.add_cog(Economy(client))