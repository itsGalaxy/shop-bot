import discord, os, json
from discord.ext import commands

def is_guild():
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.send('This command only works in guild channels.')
            return False
        return True
    return commands.check(predicate)

class Cart(commands.Cog):

    def __init__(self, client):
        self.client = client

        with open('./data/shop.json', 'r') as f:
            self.items = json.load(f)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        msg_id = payload.message_id
        item = {k:v for k,v in self.items["items"].items() if v["msg_id"] == msg_id}

        ch = await self.client.fetch_channel(payload.channel_id)
        guild = await self.client.fetch_guild(626216045522190348)
        msg = await ch.fetch_message(msg_id)
        member = await guild.fetch_member(payload.user_id)
        emoji = payload.emoji

        if member.bot:
            return
        elif not item:
            if msg.embeds[0].title == "🛒 Shopping Cart":
                if emoji.name == "🗑️":
                    content = discord.Embed(title="Order Deleted", description="Your shopping cart has successfully been deleted.", color=0xe74c3c)
                    await msg.edit(embed=content)
                    self.client.delete_cart(member.id)
                elif emoji.name == "✅":
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        member: discord.PermissionOverwrite(read_messages=True)
                    }

                    category = [c for c in guild.categories if c.id == 626332364360122378]
                    try:
                        new_channel = await guild.create_text_channel(f'{member.name}-ticket', overwrites=overwrites, category=category)
                    except:
                        print("Not enough permissions")

                    [items, total_prc] = self.client.get_cart(member.id)

                    cart = discord.Embed(title="🛒 Shopping Cart", color=0x2ecc71, description="""This is your shopping cart.\nReact with ✅ to checkout or with 🗑️ to delete your order.""")
                    cart.add_field(name="Information",value=f'**Name:** <@{str(member.id)}>',inline=False)
                    cart.add_field(name="Items",value=items, inline=True)
                    cart.add_field(name="Total Price", value=f'${str(total_prc)}', inline=True)
                    await new_channel.send(content=f'<@{str(member.id)}>', embed= cart)


            return
        else:

            [data] = item.values()

            await msg.remove_reaction(emoji, member)

            if emoji.name == "🛒":
                await self.add_to_cart(member, item)
            elif emoji.name == "🗑️":
                await self.remove_cart(member, item)

    async def add_to_cart(self, member, item):
        [name] = item.keys()
        self.client.add_cart(member.id, name)

        [items, total_prc] = self.client.get_cart(member.id)

        cart = discord.Embed(title="🛒 Shopping Cart", color=0x2ecc71, description="""This is your shopping cart.\nReact with ✅ to checkout or with 🗑️ to delete your order.""")
        cart.add_field(name="Information",value=f'**Name:** <@{str(member.id)}>',inline=False)
        cart.add_field(name="Items",value=items, inline=True)
        cart.add_field(name="Total Price", value=f'${str(total_prc)}', inline=True)

        msg = await member.send(embed=cart)
        await msg.add_reaction('✅')
        await msg.add_reaction('🗑️')

    async def remove_cart(self, member, item):
        [name] = item.keys()
        self.client.remove_cart(member.id, name)
        await member.dm_channel.send(f'```You have successfully removed {name} from your cart.```')

    @commands.command(alias=["add"])
    @is_guild()
    @commands.has_permissions(administrator=True)
    async def add_item(self, ctx, name, image, price=0.25, desc=""):
        await ctx.message.delete()
        if type(price) is str:
            price = float(price)

        if not desc:
            desc = name

        item = discord.Embed(title=name, color=0x2ecc71)
        item.set_image(url=image)
        price_str = f'${str(price)}'
        item.add_field(name="Description",value=desc, inline=True)
        item.add_field(name="Price", value=price_str, inline=True)
        msg = await ctx.send(embed=item)

        self.items["items"][name] = {
            "price": price,
            "image": image,
            "desc": desc,
            "msg_id": msg.id,
            "channel_id": msg.channel.id

        }

        await msg.add_reaction('🛒')
        await msg.add_reaction('🗑️')

        with open('./data/shop.json', 'w') as file:
            json.dump(self.items, file)

    @commands.command(alias=["remove"])
    @is_guild()
    @commands.has_permissions(administrator=True)
    async def remove_item(self, ctx, name):
        value = ""
        try:
            value = self.items["items"].pop(name)
        except KeyError:
            return ctx.send("That item does not exist.")

        ch = await self.client.fetch_channel(value["channel_id"])
        msg_to_del = await ch.fetch_message(value["msg_id"])
        await msg_to_del.delete()

        with open('./data/shop.json', 'w') as file:
            json.dump(self.items, file)

        await ctx.author.send(f'{name} has been remove from the shop successfully.')

def setup(client):
    client.add_cog(Cart(client))
