import discord
import os
import pymongo
from datetime import date
from discord.ext import commands
from dotenv import load_dotenv 
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
		#INSERT NEW TASK
		db.tasks.update_one(
			{'_id': ctx.message.author.id},
			{'$push': {'tasks': {'taskName': task, 'timeAccumulated': 0, 'commits': []}}}
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
		#REMOVE EXISTING TASK
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
		
@bot.command(brief = "Logs time for a specified task")
async def logtask(ctx, task, time_in_minutes: int):
	#CHECK IF TASK IS ALREADY IN THE DATABASE
	cur = db.tasks.find({'_id': ctx.message.author.id, 'tasks.taskName': task})
	res = list(cur)
	
	if len(res) != 0:
		#GET TODAY'S DATE
		today = date.today().strftime("%Y-%m-%d")
	
		#CHECK IF WE'VE ALREADY LOGGED TODAY ONCE
		cur = db.tasks.find({'_id': ctx.message.author.id, 'tasks': {'$elemMatch': {'taskName': task,'commits': {'$elemMatch': {'date': today,}}}}})
		res = list(cur)
		if len(res) != 0:
			#UPDATE THE EXISTING LOG
			db.tasks.update_one(
				{'_id': ctx.message.author.id},
				{'$inc': {'tasks.$[tasks].commits.$[commits].time': time_in_minutes, 'tasks.$[tasks].timeAccumulated': time_in_minutes}},
				array_filters = [{'tasks.taskName': task}, {'commits.date': today}]
			)
		else:
			#INSERT A NEW LOG FOR TODAY
			db.tasks.update_one(
				{'_id': ctx.message.author.id, 'tasks.taskName': task},
				{
					'$push': 
						{'tasks.$.commits': {'date': today, 'time': time_in_minutes}},
					'$inc':
						{'tasks.$.timeAccumulated': time_in_minutes}
				}
			)
		await ctx.send('Logged successfully. {} minutes logged for "{}"'.format(time_in_minutes, task))		
	else:
		await ctx.send('Task \"{}\" does not exist. Please input a valid task name or add a task using ?addtask'.format(task))
		
@logtask.error
async def logtask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief = "Lists all registered tasks")
async def listtasks(ctx):
	list = db.tasks.find({'_id': ctx.message.author.id}).distinct('tasks.taskName')
	output = ', '.join(map(str, list))
	await ctx.send('Current tasks are: {}'.format(output))
		
@listtasks.error
async def listtasks_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
@bot.command(brief = "Gives statistics for your tasks")
async def taskstats(ctx, task = None, filter = None):
	out = ['Some stats for your tasks:']
	list = db.tasks.find({'_id': ctx.message.author.id}).distinct('tasks')
	for dict in list:
		out.append('{}: {} minutes'.format(dict.get('taskName'), dict.get('timeAccumulated')))
	await ctx.send('\n'.join(out))

@taskstats.error
async def taskstats_error(ctx, error):
	if isinstance(error, commands.MissingRequireArgument):
		await ctx.send('Invalid arguments! Please use ?help for further information')
		
		
bot.run(DISCORD_TOKEN)