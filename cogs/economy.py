import discord
from discord.ext import commands
import random
import aiosqlite
import time
import asyncio
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class Economy(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def makefile(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS economy (UserID INT, Money Float, Daily INT)"
            )
            await db.commit()
            await db.execute(
                "CREATE TABLE IF NOT EXISTS Baking (UserID INT, Amount_Baking,TimeIn INT,Timeout INT)"
            )
            await db.commit()
            await db.execute("ALTER TABLE economy ADD COLUMN lastvoted INT")
            await db.commit()
            await ctx.send("file made oh lord")

    @commands.slash_command()
    async def bal(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute(
                "SELECT money FROM economy WHERE UserID = ?", (user.id,)
            )
            data = await data.fetchone()
            if data is None:
                await db.execute(
                    "INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",
                    (user.id, 0, 0),
                )
                await db.commit()
                await ctx.respond("You have no donuts")
            else:
                await ctx.respond(f"You have {round(data[0],2)} Donuts 🍩")

    @commands.slash_command()
    async def daily(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            user = ctx.author
            data = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (user.id,)
            )
            data = await data.fetchone()
            if data is None:
                await db.execute(
                    "INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",
                    (user.id, 5, time.time()),
                )
                await db.commit()
                await ctx.respond("You have claimed your daily and now have 5 Donuts 🍩")
            else:
                if time.time() - data[2] >= 86400:
                    dailyadding = random.randint(5, 10)
                    await db.execute(
                        "UPDATE economy SET Money = ?,daily =? WHERE UserID = ?",
                        (data[1] + dailyadding, time.time(), ctx.author.id),
                    )
                    await ctx.respond(
                        f"You have claimed your daily and now have {data[1] + dailyadding} 🍩"
                    )
                    await db.commit()
                else:
                    await ctx.respond(
                        f"You have to wait {round(int(86400 - (time.time() - data[2]))/3600,2)} hours to claim your daily 🍩"
                    )

    @commands.slash_command()
    async def bal_top(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute(
                "SELECT * FROM economy ORDER BY Money DESC LIMIT 10"
            )
            data = await data.fetchall()
            embed = discord.Embed(title="Top 10 Donut Holders", color=0x00FF00)
            for i in range(len(data)):
                user = await self.client.fetch_user(data[i][0])
                embed.add_field(
                    name=f"{i + 1}. {user}",
                    value=f"{round(data[i][1],2)} Donuts 🍩",
                    inline=False,
                )
            await ctx.respond(embed=embed)
        # get the users money and display it and the total value of there stocks and the total value of there stocks and money

    @commands.slash_command()
    async def send(self, ctx, user: discord.Member, amount: int):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            userto = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (user.id,)
            )
            userfrom = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,)
            )
            userto = await userto.fetchone()
            userfrom = await userfrom.fetchone()
            if userto == userfrom:
                await ctx.respond("You cant send to your self")
                return
            if amount <= 0:
                await ctx.respond("You cant send a negative amount")
                return
            if userfrom[1] < amount:
                await ctx.respond("You dont have enough money to send that")
                return
            await ctx.respond(f"Transaction protocol starting... ", ephemeral=True)
            msg = await ctx.channel.send(
                f"{ctx.author.mention} is about to give {user} {amount} Donuts 🍩. React with ✅ to confirm or ❌ to cancel."
            )
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, usercheck):
                return (
                    usercheck == ctx.author
                    and str(reaction.emoji) in ["✅", "❌"]
                    and reaction.message == msg
                )

            try:
                reaction, usercheck = await self.client.wait_for(
                    "reaction_add", timeout=30.0, check=check
                )
            except asyncio.TimeoutError:
                await msg.edit(content="Confirmation timed out.")
                await msg.remove_reaction("✅", self.client.user)
                await msg.remove_reaction("❌", self.client.user)
                return

            if str(reaction.emoji) == "✅":
                await msg.edit(content=f"You have given {user} {amount} Donuts 🍩")
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        userto[1] + amount,
                        user.id,
                    ),
                )
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        userfrom[1] - amount,
                        ctx.author.id,
                    ),
                )
                await db.commit()
            else:
                await msg.edit(content="Transaction cancelled.")
            await msg.clear_reactions()

    @commands.slash_command()
    async def rps(self, ctx, choice: str, amount: int):
        # gamble with rock paper scissors
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,)
            )
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
                        await ctx.respond(
                            "Invalid choice. Please choose rock, paper, or scissors."
                        )
                    else:
                        bot_choice = random.choice(choices)
                        result = None
                        if choice == bot_choice:
                            result = "tie"
                        elif (
                            (choice == "rock" and bot_choice == "scissors")
                            or (choice == "paper" and bot_choice == "rock")
                            or (choice == "scissors" and bot_choice == "paper")
                        ):
                            result = "win"
                        else:
                            result = "lose"

                        new_balance = data[1]
                        if result == "win":
                            new_balance += int(amount * 1.5)
                            await db.execute(
                                "UPDATE economy SET Money = ? WHERE UserID = ?",
                                (
                                    new_balance,
                                    ctx.author.id,
                                ),
                            )
                            await db.commit()
                        if result == "lose":
                            await db.execute(
                                "UPDATE economy SET Money = ? WHERE UserID = ?",
                                (
                                    data[1] - amount,
                                    ctx.author.id,
                                ),
                            )
                            await db.commit()

                        if result == "tie":
                            await ctx.respond(f"Bot chose {bot_choice}. It's a tie!")
                        elif result == "win":
                            await ctx.respond(
                                f"Bot chose {bot_choice}. You won {int(amount * 1.5)} donuts! Your new balance is {new_balance + int(amount * 1.5)}."
                            )
                        else:
                            await ctx.respond(
                                f"Bot chose {bot_choice}. You lost {amount} donuts. Your new balance is {new_balance - amount}."
                            )

    @commands.slash_command()
    async def bake(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            money = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,)
            )
            money = await money.fetchone()

            Baking = await db.execute(
                "SELECT * FROM Baking WHERE UserID = ?", (ctx.author.id,)
            )
            Baking = await Baking.fetchone()
            mins = random.randint(30, 120)
            # if baking does not exist set userID, amount to 1, and timein to current time and time out to current time + 5 minutes
            if Baking is None:
                if money is None:
                    await db.execute(
                        "INSERT OR IGNORE INTO economy (UserID,Money,daily)  VALUES (?, ?,?)",
                        (ctx.author.id, 0, 0),
                    )
                    await db.commit()
                    await ctx.respond("You have no donuts")
                    return

                # ask the user how many donuts they want to bake
                await ctx.respond(
                    "How many donuts batch do you want to bake? note it costs 5 donuts to bake 1 batch"
                )

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                msg = await self.client.wait_for("message", check=check)
                amount = msg.content

                if amount.isnumeric() == False:
                    await ctx.respond("You can only bake a number")
                    return
                amount = int(amount)
                if amount <= 0:
                    await ctx.respond("You can't bake a negative amount or nothing")
                    return
                if amount > 90:
                    await ctx.respond("You can't bake more than 90 donuts at a time")
                    return

                amount = amount * 5
                if money[1] < amount:
                    await ctx.respond("You don't have enough donuts")
                    return

                moneyset = money[1] - amount
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        moneyset,
                        ctx.author.id,
                    ),
                )
                await db.commit()
                await db.execute(
                    "INSERT OR IGNORE INTO Baking (UserID,Amount_Baking,timein,timeout)  VALUES (?, ?,?,?)",
                    (ctx.author.id, amount, time.time(), time.time() + mins * 60),
                )
                await db.commit()
                await ctx.respond(
                    f"You have started baking {amount} donuts they will be done in {mins} minutes. Use /bake again to take them out of the oven \n if you take them out of the oven on time you make 50% more donuts. If you take then out with in 10 minutes you make 20% more donuts"
                )
                return
            # if there is food in the oven and the time to take out is plus or minus from 2 minutes of the current time give the user 1.5x the amount of donuts then remove the collum from the database
            if Baking[3] < time.time() + 2 * 60 and Baking[3] > time.time() - 2 * 60:
                amountgiving = Baking[1] * 1.5
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        money[1] + amountgiving,
                        ctx.author.id,
                    ),
                )
                await db.execute(
                    "DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,)
                )
                await db.commit()
                await ctx.respond(f"You have finished baking {Baking[1] * 1.5} donuts")
                return
            if Baking[3] < time.time() + 10 * 60 and Baking[3] > time.time() - 10 * 60:
                amountgiving = Baking[1] * 1.1
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        money[1] + amountgiving,
                        ctx.author.id,
                    ),
                )
                await db.execute(
                    "DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,)
                )
                await db.commit()
                await ctx.respond(
                    f"You have finished baking but you just missed the perfect moment. You made {Baking[1] * 1.1} donuts"
                )
                return
            # if the food is taken out to soon give the user nothing and remove the collum from the database. Tell them they took it out to soon
            if Baking[3] > time.time():
                await db.execute(
                    "DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,)
                )
                await db.commit()
                await ctx.respond(
                    f"You took out your food to soon and it raw. You made no donuts"
                )
                return
            # if the food is taken out to late give the user nothing and remove the collum from the database. Tell them they took it out to soon
            if Baking[3] < time.time():
                await db.execute(
                    "DELETE FROM Baking WHERE UserID = ?", (ctx.author.id,)
                )
                await db.commit()
                await ctx.respond(
                    f"You took out your food to late and it burnt. You made no donuts"
                )
                return

    @commands.slash_command()
    async def vote(self, ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            tocken = os.getenv("TOPGG_TOKEN")
            api = requests.get(
                f"https://top.gg/api/bots/902240397273743361/check?userId={ctx.author.id}",
                headers={"Authorization": tocken, "Content-Type": "application/json"},
            )
            data = api.json()
            print(api)
            print(data)
            voted = data["voted"]
            # if the api does not return a 200 status code
            if api.status_code != 200:
                voted = 1
                print("api error")
            if voted == 0:
                await ctx.respond(
                    "You need to have voted for simplex in the last 24 hours to claim these coins. Please vote and then try again, you can vote here: https://top.gg/bot/902240397273743361/vote",
                    ephemeral=True,
                )
                return
            data = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,)
            )
            data = await data.fetchone()
            if data is None:
                await db.execute(
                    "INSERT OR IGNORE INTO economy (UserID,Money,daily,lastvoted)  VALUES (?, ?,?,?)",
                    (ctx.author.id, 0, 0, 0),
                )
                return
            # is the user has already voted in the last 24 hours tell them they have already voted if not give them 10 donuts and set last voted to current time
            if data[3] is None:
                cash = random.randint(5, 20)
                await db.execute(
                    "UPDATE economy SET Money = ? WHERE UserID = ?",
                    (
                        data[1] + cash,
                        ctx.author.id,
                    ),
                )
                await db.commit()
                await db.execute(
                    "UPDATE economy SET lastvoted = ? WHERE UserID = ?",
                    (
                        time.time(),
                        ctx.author.id,
                    ),
                )
                await db.commit()
                await ctx.respond(
                    f"You have voted and recieved {cash} donuts", ephemeral=True
                )
                return

            if data[3] > time.time() - 86400:
                await ctx.respond(
                    "You have already voted in the last 24 hours", ephemeral=True
                )
                return
            cash = random.randint(5, 20)
            await db.execute(
                "UPDATE economy SET Money = ? WHERE UserID = ?",
                (
                    data[1] + cash,
                    ctx.author.id,
                ),
            )
            await db.execute(
                "UPDATE economy SET lastvoted = ? WHERE UserID = ?",
                (
                    time.time(),
                    ctx.author.id,
                ),
            )
            await db.commit()
            await ctx.respond(
                f"You have voted and recieved {cash} donuts", ephemeral=True
            )
            return

    @commands.slash_command()
    async def roulette(self, ctx, option: str, amount: int):
        userid = ctx.author.id
        roulette_wheel = [
            (0, "green"),
            (32, "red"),
            (15, "black"),
            (19, "red"),
            (4, "black"),
            (21, "red"),
            (2, "black"),
            (25, "red"),
            (17, "black"),
            (34, "red"),
            (6, "black"),
            (27, "red"),
            (13, "black"),
            (36, "red"),
            (11, "black"),
            (30, "red"),
            (8, "black"),
            (23, "red"),
            (10, "black"),
            (5, "red"),
            (24, "black"),
            (16, "red"),
            (33, "black"),
            (1, "red"),
            (20, "black"),
            (14, "red"),
            (31, "black"),
            (9, "red"),
            (22, "black"),
            (18, "red"),
            (29, "black"),
            (7, "red"),
            (28, "black"),
            (12, "red"),
            (35, "black"),
            (3, "red"),
            (26, "black"),
        ]

        async with aiosqlite.connect("datebases/donuts.db") as db:
            if amount < 1:
                await ctx.respond("You need to bet more than 1 donut", ephemeral=True)
                return

            data = await db.execute("SELECT * FROM economy WHERE UserID = ?", (userid,))
            data = await data.fetchone()
            if data is None:
                await db.execute(
                    "INSERT OR IGNORE INTO economy (UserID,Money,daily,lastvoted)  VALUES (?, ?,?,?)",
                    (userid, 0, 0, 0),
                )
                await ctx.respond("You don't have any donuts", ephemeral=True)
                return

            if data[1] < amount:
                await ctx.respond("You don't have enough donuts", ephemeral=True)
                return

            option = option.lower()
            if option not in ["red", "black", "green"] and not option.isdigit():
                await ctx.respond("You need to pick a valid color or number", ephemeral=True)
                return

            await db.execute(
                "UPDATE economy SET Money = ? WHERE UserID = ?",
                (
                    data[1] - amount,
                    userid,
                ),
            )
            await db.commit()

            # Perform the roulette spin animation
            await ctx.respond("Spinning the roulette wheel...")
            await asyncio.sleep(3)  # Wait for 3 seconds for the animation

            # Simulate the spinning and landing on a result
            result = random.choice(roulette_wheel)
            await asyncio.sleep(2)  # Wait for 2 seconds for the animation to stop

            if option.isdigit():
                if int(option) == result[0]:
                    await db.execute(
                        "UPDATE economy SET Money = ? WHERE UserID = ?",
                        (
                            data[1] + amount * 36,
                            userid,
                        ),
                    )
                    await db.commit()
                    await ctx.respond(f"You won {amount * 10} donuts! 🎉")
                else:
                    await ctx.respond(f"You lost {amount} donuts! 😢")
            else:
                if result[1] == option:
                    if option == "green":
                        await db.execute(
                            "UPDATE economy SET Money = ? WHERE UserID = ?",
                            (
                                data[1] + amount * 10,
                                userid,
                            ),
                        )
                        await db.commit()
                        await ctx.respond(f"You won {amount * 10} donuts")
                        return
                    else:
                        await db.execute(
                            "UPDATE economy SET Money = ? WHERE UserID = ?",
                            (
                                data[1] + amount * 2,
                                userid,
                            ),
                        )
                        await db.commit()
                        await ctx.respond(f"You won {amount * 2} donuts")
                        return
                else:
                    await ctx.respond(f"You lost {amount} donuts")
                    return

    @commands.command()
    @commands.is_owner()
    async def force_add(self, ctx, user: discord.Member, amount: int):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            data = await db.execute(
                "SELECT * FROM economy WHERE UserID = ?", (user.id,)
            )
            data = await data.fetchone()
            await db.execute(
                "UPDATE economy SET Money = ? WHERE UserID = ?",
                (
                    amount,
                    user.id,
                ),
            )
            await db.commit()
            await ctx.send("done")


def setup(client):
    client.add_cog(Economy(client))
