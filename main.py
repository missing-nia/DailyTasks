import discord
import os
from dotenv import load_dotenv 
from discord.ext import commands

load_dotenv()

#GRAP THE API TOKEN FROM THE .ENV FILE
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='?')
	
@bot.command(brief="Adds a specified task")
async def addtask(ctx, task):
		await ctx.send('Added task \"{}\"'.format(task))
		
@addtask.error
async def addtask_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief="Removes a specified task")
async def removetask(ctx, task):
		await ctx.send('Removed task \"{}\"'.format(task))
		
@removetask.error
async def removetask_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief="Checks in to a specified task")
async def checkin(ctx, task, time_in_minutes: int):
		await ctx.send('Checked in successfully. {} minutes logged for "{}"'.format(time_in_minutes, task))
		
@checkin.error
async def checkin_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief="Lists all registered tasks")
async def listtasks(ctx):
		await ctx.send('Current tasks are:')
		
@listtasks.error
async def listtasks_error(ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send('Invalid arguments! Please use ?help for further information')
		
bot.run(DISCORD_TOKEN)