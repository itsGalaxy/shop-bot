import discord
from discord.ext import commands
import os, json
import sqlite3

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './data/cart.sqlite3')

class Bot(commands.Bot):

    def __init__(self, command_prefix, *args, **kwargs):

        con = sqlite3.connect(DEFAULT_PATH)
        cursor = con.cursor()
        cursor.execute("create table if not exists cart (id integer PRIMARY KEY, user_id integer, item text NOT NULL, quantity integer, UNIQUE(user_id, item))")

        con.commit()
        cursor.close()
        con.close()

        super().__init__(*args, command_prefix=command_prefix, **kwargs)

    async def on_ready(self):
        print(f'Loaded {self.user.name}')
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')
                print(f'{filename} loaded.')

    @staticmethod
    def add_cart(user_id:int, item:str, quantity=1):
        con = sqlite3.connect(DEFAULT_PATH)
        cursor = con.cursor()

        try:
            cursor.execute('insert into cart (user_id, item, quantity) values (?, ?, ?)', [user_id, item, quantity])
        except:
            cursor.execute('update cart set quantity = quantity + ? where user_id = ? and item = ?', [quantity, user_id, item])

        con.commit()
        cursor.close()
        con.close()

    @staticmethod
    def remove_cart(user_id:int, item:str):
        con = sqlite3.connect(DEFAULT_PATH)
        cursor = con.cursor()
        cursor.execute('delete from cart where user_id = ? and item = ?', [user_id, item])

        con.commit()
        cursor.close()
        con.close()

    @staticmethod
    def delete_cart(user_id: int):
        con = sqlite3.connect(DEFAULT_PATH)
        cursor = con.cursor()
        cursor.execute('delete from cart where user_id = ?', [user_id])

        con.commit()
        cursor.close()
        con.close()

    @staticmethod
    def get_cart(user_id:int):
        con = sqlite3.connect(DEFAULT_PATH)
        cursor = con.cursor()
        items = ''
        total_prc = 0.0
        with open('./data/shop.json', 'r') as f:
            shop = json.load(f)["items"]

        for row in cursor.execute('select * from cart where user_id = ?', [user_id]):
            if len(row) == 4:
                items += f'x{str(row[3])} {row[2]}\n'
                item = {k:v for k,v in shop.items() if k == row[2]}
                total_prc += row[3]*item[row[2]]["price"]

        con.commit()
        cursor.close()
        con.close()

        return items, total_prc

    @staticmethod
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(error)


if __name__ == "__main__":

    client = Bot(command_prefix=".");
    with open('./data/config.json', 'r') as f:
        client.run(json.load(f)["token"])


@client.check
async def ignore_bots(ctx):
    return ctx.author.bot == False
