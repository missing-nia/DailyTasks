import discord
import os
import pymongo
from datetime import date
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv 
from pymongo import MongoClient
from typing import Optional


#DATE DIFFERENCE FUNCTION
def date_diff(d1, d2):
	d1 = datetime.strptime(d1, "%Y-%m-%d")
	d2 = datetime.strptime(d2, "%Y-%m-%d")
	return abs((d2-d1).days)

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

#DATABASE FIND
#DECLARING HERE SO WE CAN USE "db"
def in_db(query):
    cur = db.tasks.find(query)
    res = list(cur)
    if len(res) != 0:
        return True
    return False
    

#DISCORD BOT COMMANDS	
@bot.command(brief = "Adds a specified task")
async def addtask(ctx, task: str):
	#CHECK IF THE USER IS IN THE DATABASE (ONE-TIME SETUP)
	if in_db({'_id': ctx.message.author.id}) == False:
		db.tasks.insert_one({'_id': ctx.message.author.id, 'tasks':[]})

	#CHECK IF TASK IS ALREADY IN THE DATABASE
	if in_db({'_id': ctx.message.author.id, 'tasks.taskName': task}) == True:
		await ctx.send('Task `{}` already exists. Please choose a different name or remove existing task using `?removetask`'.format(task))
	else:
		#INSERT NEW TASK
		db.tasks.update_one(
			{'_id': ctx.message.author.id},
			{'$push': {'tasks': {'taskName': task, 'timeAccumulated': 0, 'commits': []}}}
		)
		await ctx.send('Added task `{}`'.format(task))
		
@addtask.error
async def addtask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')
		
@bot.command(brief = "Removes a specified task")
async def removetask(ctx, task: str):
	#CHECK IF TASK IS IN THE DATABASE
	if in_db({'_id': ctx.message.author.id, 'tasks.taskName': task}) == True:
		#REMOVE EXISTING TASK
		db.tasks.update_one(
			{'_id': ctx.message.author.id},
			{'$pull': {'tasks': {'taskName': task}}}
		)
		await ctx.send('Removed task `{}`'.format(task))
	else:
		await ctx.send('Task `{}` does not exist. Please input a valid task name or add a task using `?addtask`'.format(task))
		
@removetask.error
async def removetask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')
		
@bot.command(brief = "Logs time for a specified task")
async def logtask(ctx, task: str, time_in_minutes: int):
	#CHECK IF TASK IS ALREADY IN THE DATABASE
	if in_db({'_id': ctx.message.author.id, 'tasks.taskName': task}) == True:
		#GET TODAY'S DATE
		today = date.today().strftime("%Y-%m-%d")
	
		#CHECK IF WE'VE ALREADY LOGGED TODAY ONCE
		if in_db({'_id': ctx.message.author.id, 'tasks': {'$elemMatch': {'taskName': task,'commits': {'$elemMatch': {'date': today,}}}}}) == True:
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
		await ctx.send('Logged successfully. `{}` minutes logged for `{}`'.format(time_in_minutes, task))		
	else:
		await ctx.send('Task `{}` does not exist. Please input a valid task name or add a task using `?addtask`'.format(task))
		
@logtask.error
async def logtask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')
		
@bot.command(brief = "Lists all registered tasks")
async def listtasks(ctx):
	list = db.tasks.find({'_id': ctx.message.author.id}).distinct('tasks.taskName')
	output = '```\n' + '\n'.join(map(str, list)) + '```'
	await ctx.send('Current tasks are: {}'.format(output))
		
@listtasks.error
async def listtasks_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')
		
@bot.command(brief = "Gives statistics for your tasks")
async def taskstats(ctx, user: Optional[discord.Member], task: Optional[str], days: Optional[int]):
	#CHECK IF ANYONE WAS MENTIONED OTHERWISE USE THE AUTHOR ID
	if user is None:
		user = ctx.message.author
	
	out = ['Some stats for your tasks: ```']
	taskList = db.tasks.find({'_id': user.id}).distinct('tasks')
	
	#CHECK THAT THE USER ACTUALLY HAS TASKS
	if len(taskList) == 0:
		out = ['No tasks available']
	
	if task:
		taskList = [x for x in taskList if x['taskName'] == task]
		
		#CHECK THAT THE TASK QUERY WAS VALID
		if len(taskList) == 0:
			out = ['Task `{}` does not exist. Please input a valid task name or add a task using `?addtask`']
	
	if len(taskList) > 0:
		#GET STATS FOR TASK(S)
		for dict in taskList:
			if days:
				#GET COMMITS FOR THE NUMBER OF DAYS REQUESTED
				intDays = int(days)	
			
				if intDays <= 0:
					out = ['Invalid number of days. Please input a number of days greater than zero']
					break
							
				commits = dict.get('commits')
				commits = [x for x in commits if date_diff(x['date'], date.today().strftime("%Y-%m-%d")) < intDays]
				time = 0
				
				for dict in commits:
					time += dict.get('time')
		
				out.append('{} minutes over {} days'.format(time, intDays))
				out.append('{} minutes average per day'.format(int(time/intDays)))
				out.append('{} days commited'.format(len(commits)))
			else:
				out.append('{}: {} minutes'.format(dict.get('taskName'), dict.get('timeAccumulated')))		
		out.append('```')
	await ctx.send('\n'.join(out))

@taskstats.error
async def taskstats_error(ctx, error):
	if isinstance(error, commands.MissingRequireArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')

@bot.command(brief = "Renames a task")
async def renametask(ctx, old_task_name: str, new_task_name: str):
	#CHECK IF THE TASK IS IN THE DATABASE
    if in_db({'_id': ctx.message.author.id, 'tasks.taskName': old_task_name}) == True:
        #MAKE SURE WE DONT CHANGE TO AN EXISTING TASK NAME
        if in_db({'_id': ctx.message.author.id, 'tasks.taskName': new_task_name}) == True:
            await ctx.send('Task `{}` already exists! Please choose a different name'.format(new_task_name))     
        else:
            #UPDATE THE TASK NAME
            db.tasks.update_one(
                {'_id': ctx.message.author.id, 'tasks.taskName': old_task_name},
                {'$set': {'tasks.$.taskName': new_task_name}}
            )		
            await ctx.send('Task `{}` renamed to `{}` successfully.'.format(old_task_name, new_task_name))
    else:
        await ctx.send('Task `{}` does not exist. Please input a valid task name or add a task using `?addtask`'.format(old_task_name))
		
@renametask.error
async def renametask_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send('Invalid arguments! Please use `?help` for further information')
		
bot.run(DISCORD_TOKEN)