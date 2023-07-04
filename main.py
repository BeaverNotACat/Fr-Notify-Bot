import os
import json

import grequests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


class MissingEnvironmentVariable(Exception):
    pass


class UserAlreadyRegistered(Exception):
    pass


class Task:
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __eq__(self, item):
        if isinstance(item, Task):
            return self.url == item.url
        else:
            return False
    
    def __repr__(self):
        return self.title

    def __str__(self):
        return self.title
        

class HabrUpdatesCheker:
    def __init__(self):
        self.seen_tasks = []
        try:
            self.buffer_size = int(os.environ['CHEKER_BUFFER_SIZE'])
        except KeyError:
            raise MissingEnvironmentVariable(
                'Sowwy b-but... CHEKER_BUFFER_SIZE does not exists')
        try:
            self.tasks_url = os.environ['TASKS_URL']
        except KeyError:
            raise MissingEnvironmentVariable(
                'Sowwy b-but... TASKS_URL does not exists')

    def _cut_seen_tasks(self):
        while len(self.seen_tasks) > self.buffer_size:
            self.seen_tasks.pop()

    async def _get_tasks_soup(self):
        req = [grequests.get(self.tasks_url)]
        html = grequests.map(req)[0].text
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all('article', class_='task')
    
    async def _get_tasks(self) -> list[Task]:
        tasks = []
        for html in await self._get_tasks_soup():
            title = html.find('div', class_='task__title')
            task = Task(
                title=title.text,
                url=self.tasks_url + title.find('a')['href'])
            tasks.append(task)
        return tasks
    
    async def get_new_taks(self):
        new_tasks = []
        for task in await self._get_tasks():
            if task not in self.seen_tasks:
                self.seen_tasks.append(task)
                new_tasks.append(task)
        self._cut_seen_tasks()
        return new_tasks
    

class SubscribtionsManager:
    def __init__(self):
        with open('subscriptions.json', 'r+') as file:
            self._subscriptions = json.load(file)
    
    @property
    def subscriptions(self):
        return self._subscriptions
    
    def add_subsription(self, subscription):
        if subscription in self.subscriptions:
            raise UserAlreadyRegistered

        self.subscriptions.add(subscription)
        with open('subscriptions.json', 'w') as file:
            json.dump(self.subscriptions, file)


def taskview(task: Task):
    return f'Masteww, new task awwived!\n{task.title}\n{task.url}'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        SubscribtionsManager().add_subsription(
            { "chat_id": update.effective_message.chat_id})
        await update.message.reply_text(
            'Hello! U have subscwibed :3')

    except UserAlreadyRegistered:
        await update.message.reply_text(
            'Sowwy u already subscwibed U_U')


async def notify_about_new_tasks(
        context: ContextTypes.DEFAULT_TYPE):
    global client
    for task in await client.cheker.get_new_taks():
        for subscription in client.subscriptions.subscriptions:
            await context.bot.send_message(
                chat_id=subscription['chat_id'],
                text=taskview(task))


class Client():
    def __init__(self):
        try:
            token = os.environ['TOKEN']
        except KeyError:
            raise MissingEnvironmentVariable(
                'Ow, nooo "TOKEN" does not exist :sad owo:')
        self.application = Application.builder().token(token).build()
        self.cheker = HabrUpdatesCheker()
        self.subscriptions = SubscribtionsManager()

    def run(self):
        self.application.add_handler(CommandHandler("start", start))
        self.application.job_queue.run_repeating(
            notify_about_new_tasks, interval=10) 
        self.application.run_polling()


if __name__ == "__main__":
    load_dotenv()
    client = Client()
    client.run()
    
