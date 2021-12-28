import discord
import os
import pymongo
from dotenv import load_dotenv 
from discord.ext import commands
from pymongo import MongoClient

load_dotenv()

#GRAP THE API TOKEN FROM THE .ENV FILE
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#INITIALIZE THE BOT
bot = commands.Bot(command_prefix='?')

#CONNECT TO THE DATABASE
uri = os.getenv("DATABASE_URL")
cluster = MongoClient(uri)

db = cluster["daily_tasks"]

collection = db["daily_tasks"]

#TEST MONGODB
#NOTE: SHOULD CHECK FOR EXISTING DATA BEFORE ATTEMPTING TO INSERT IN FINISHED CODE
#testdata = {"_id": 39403490, "tasks": [{"taskName": "homework", "timeAccumulated": 300, "commits": [{"date": "01-12-1997", "time": 65}]}]}
#tasks = db.tasks
#tasks.insert_one(testdata)

#TEST UPDATING DATA
#db.tasks.update_one(
	#{'_id': 39403490, 'tasks.taskName': 'homework'},
	#{'$push': {'tasks.$.commits': {"date": "01-13-1997", "time": 50}}})


#DISCORD BOT COMMANDS	
@bot.command(brief = "Adds a specified task")
async def addtask(ctx, task):
	#CHECK IF THE USER IS IN THE DATABASE (ONE-TIME SETUP)
	cur = db.tasks.find({'_id': ctx.message.author.id})
	res = list(cur)
	
	if len(res) == 0:
		db.tasks.insert_one({'_id': ctx.message.author.id, 'tasks':[]})

	#CHECK IF TASK IS ALREADY IN THE DATABASE
	cur = db.tasks.find({'_id': ctx.message.author.id, 'tasks.taskName': task})
	res = list(cur)
	
	if len(res) != 0:
		await ctx.send('Task \"{}\" already exists. Please choose a different name or remove existing task using ?removetask'.format(task))
	else:
		db.tasks.update_one(
			{'_id': ctx.message.author.id},
			{'$push': {'tasks': {"taskName": task, "timeAccumulated": 0, "commits": []}}}
		)
		await ctx.send('Added task \"{}\"'.format(task))
		
@addtask.error
async def addtask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief = "Removes a specified task")
async def removetask(ctx, task):
	#CHECK IF TASK IS IN THE DATABASE
	cur = db.tasks.find({'_id': ctx.message.author.id, 'tasks.taskName': task})
	res = list(cur)
	
	if len(res) != 0:
		db.tasks.update_one(
			{'_id': ctx.message.author.id},
			{'$pull': {'tasks': {'taskName': task}}}
		)
		await ctx.send('Removed task \"{}\"'.format(task))
	else:
		await ctx.send('Task \"{}\" does not exist. Please input a valid task name or add a task using ?addtask'.format(task))
		
@removetask.error
async def removetask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief = "Checks in to a specified task")
async def checkin(ctx, task, time_in_minutes: int):
	await ctx.send('Checked in successfully. {} minutes logged for "{}"'.format(time_in_minutes, task))
		
@checkin.error
async def checkin_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief = "Lists all registered tasks")
async def listtasks(ctx):
	await ctx.send('Current tasks are:')
		
@listtasks.error
async def listtasks_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
bot.run(DISCORD_TOKEN)