import discord
from discord.ext import commands,tasks
import random
import aiosqlite
import time


class stocks(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.stock_fluctuator.start()


    @commands.slash_command()
    @commands.is_owner()
    async def makefile_stocks(self,ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS stocks (Symbol, value Float)")
            await db.commit()
            await ctx.send("file made oh lord")
            await db.execute("CREATE TABLE IF NOT EXISTS User_stocks (user_id INTEGER,Symbol, num_shares INTEGER,purchase_price Float)")
            await db.commit()

    @commands.slash_command()
    @commands.is_owner()
    async def add_stock(self,ctx,symbol,startvalue):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            await db.execute("INSERT OR IGNORE INTO stocks (Symbol,value) VALUES(?,?)",(symbol,startvalue))
            await db.commit()
            await ctx.respond(f" I have added {symbol} to the database with a starting value of {startvalue} Donuts")

    @commands.slash_command()
    async def preview_stocks(self,ctx):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            datas = await db.execute("SELECT * FROM stocks")
            datas = await datas.fetchall()
            embed = discord.Embed(title="Current stock market")
            for i in datas:
                embed.add_field(name=i[0],value=i[1], inline=False)
            await ctx.respond(embed=embed)


    @commands.slash_command()
    async def buy_stocks(self,ctx,stock,amount):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            stockdata = await db.execute("SELECT * FROM stocks WHERE Symbol = ?",(stock,))
            stockdata = await stockdata.fetchone()
            money = await db.execute("SELECT * FROM economy WHERE UserID = ?", (ctx.author.id,))
            money = await money.fetchone()
            if money is None:
                await ctx.respond("You have no donuts")
            if amount <= 0:
                await ctx.respond("You cant buy a negative amount")
                return
            else:
                print(money[1])
                print(stockdata[1])
                if money[1] < float(stockdata[1]) * float(amount):
                    await ctx.respond("You don't have enough donuts")
                    return
                account = float(money[1] - float(stockdata[1]) * float(amount))
                await db.execute("UPDATE economy SET Money = ? WHERE UserID = ?", (account, ctx.author.id,))
                await ctx.respond(f"You have brought {amount} of the {stock}. You know have {round(account,2)} Donuts")
                total = float(stockdata[1]) * float(amount)
                await db.execute("INSERT OR IGNORE INTO User_stocks (Symbol,num_shares,user_id,purchase_price) VALUES(?,?,?,?)",(stock,amount,ctx.author.id,total,))
                await db.commit()


    @tasks.loop(seconds=10)
    async def stock_fluctuator(self):
        async with aiosqlite.connect("datebases/donuts.db") as db:
            datas = await db.execute("SELECT * FROM stocks")
            datas = await datas.fetchall()
            for data in datas:
                if random.randint(0,3) != 0:
                    prices = round(data[1] * (1+random.uniform(-0.10,0.10)),2)
                    await db.execute("UPDATE stocks SET value = ? WHERE Symbol = ?", (prices,data[0],))
                    await db.commit()


def setup(client):
    client.add_cog(stocks(client))