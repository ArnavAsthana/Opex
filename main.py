"""Importing the modules"""
import discord
from discord.ext import commands
import json
import os
import random
import keep_alive


"""Planning out command prefix and intents"""
client = commands.Bot(command_prefix = 'opex ', intents=discord.Intents.all()) 

"""Initialisers for Tic tac toe system"""
player1 = ""
player2 = ""
turn = ""
gameOver = True

board = []

winningConditions = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]

"""List of items name,price and description in the shop"""
shop_items = [{'name': 'Car','price': 100000,'description':'Travel Faster'},
             {'name': 'Bike','price': 9999,'description':'Travel'},
             {'name': 'Laptop','price': 999,'description':'Do work from home'},
             {'name': 'Phone', 'price': 999,'description':'Call and send messages'},
             {'name': 'OpeCoin', 'price': 8999,'description':'CryptoCurrency! (Fluctuates a lot!)'}]


@client.event
async def on_ready():
    print('Ready to serve')

@client.command()
async def balance(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()


    wallet_amount = users[str(user.id)]['wallet']
    bank_balance = users[str(user.id)]['bank'] 

    em1 = discord.Embed(title = f'{ctx.author.name}s balance', color = discord.Color.green())
    em1.add_field(name = 'Wallet balance', value = wallet_amount)
    em1.add_field(name = 'Bank balance', value = bank_balance)
    await ctx.send(embed = em1)

@client.command()
async def beg(ctx):
    await open_account(ctx.author)

    users = await get_bank_data()

    user = ctx.author

    earnings = random.randrange(101)

    await ctx.send(f"Lord Opex gave you {earnings} coins!!")


    users[str(user.id)]['wallet'] += earnings

    with open('mainbank.json', 'w') as f:
        json.dump(users,f)

@client.command()
async def shop(ctx):
    em1 = discord.Embed(title = 'Opex Megastore')

    for item in shop_items:
        name = item['name']
        price = item['price']
        desc = item['description']
        em1.add_field(name = name, value = f'${price} || {desc}')

    await ctx.send(embed = em1)

@client.command()
async def buy(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("First check the items in the shop then buy!")
            return
        if res[1]==2:
            await ctx.send(f"Check you wallet! {amount} {item} ||NOOB||")
            return


    await ctx.send(f"You just bought {amount} {item}. Thanks for shopping with us. Have a nice day!")

@client.command()
async def bag(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]
    except:
        bag = []


    em = discord.Embed(title = "Bag")
    for item in bag:
        name = item["item"]
        amount = item["amount"]

        em.add_field(name = name, value = amount)    

    await ctx.send(embed = em)

async def buy_this(user,item_name,amount):
    item_name = item_name.lower()
    name_ = None
    for item in shop_items:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0]<cost:
        return [False,2]


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt + amount
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            obj = {"item":item_name , "amount" : amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item":item_name , "amount" : amount}
        users[str(user.id)]["bag"] = [obj]        

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost*-1,"wallet")

    return [True,"Worked"]


@client.command()
async def sell(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await sell_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That Object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have {amount} {item} in your bag.")
            return
        if res[1]==3:
            await ctx.send(f"You don't have {item} in your bag.")
            return

    await ctx.send(f"You just sold {amount} {item}.")

async def sell_this(user,item_name,amount,price = None):
    item_name = item_name.lower()
    name_ = None
    for item in shop_items:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            if price==None:
                price = 0.9* item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt - amount
                if new_amt < 0:
                    return [False,2]
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            return [False,3]
    except:
        return [False,3]    

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost,"wallet")

    return [True,"Worked"]

@client.command(aliases = ["lb"])
async def leaderboard(ctx,x = 1):
    users = await get_bank_data()
    leader_board = {}
    total = []
    for user in users:
        name = int(user)
        total_amount = users[user]["wallet"] + users[user]["bank"]
        leader_board[total_amount] = name
        total.append(total_amount)

    total = sorted(total,reverse=True)    

    em = discord.Embed(title = f"Top {x} Richest People" , description = "This is decided on the basis of raw money in the bank and wallet",color = discord.Color(0xfa43ee))
    index = 1
    for amt in total:
        id_ = leader_board[amt]
        member = client.get_user(id_)
        name = member.name
        em.add_field(name = f"{index}. {name}" , value = f"{amt}",  inline = False)
        if index == x:
            break
        else:
            index += 1

    await ctx.send(embed = em)


@client.command()
async def withdraw(ctx, amount = None):
    await open_account(ctx.author)
    
    if amount == None:
        await ctx.send('Enter the amount first then run the command!')
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[1]:
        await ctx.send('Huh! First check your bank balance!')
        return

    if amount<0:
        await ctx.send('Enter a natural number first! ||noob||')
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author,-1 * amount, 'bank')

    await ctx.send(f'Bank: You have withdrew {amount} cash! Have a nice day!')


@client.command()

async def deposit(ctx, amount = None):
    await open_account(ctx.author)
    
    if amount == None:
        await ctx.send('Enter the amount first then run the command!')
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send('Huh! First check your wallet ||NOOB!|| !')
        return

    if amount<0:
        await ctx.send('Enter a natural number first! ||noob||')
        return

    await update_bank(ctx.author,-1*amount)
    await update_bank(ctx.author,amount, 'bank')

    await ctx.send(f'Bank: You have withdrew {amount} cash! Have a nice day!')


async def open_account(user):
    
    users = await get_bank_data()

    if str(user.id) in users:
        return False

    else:
        users[str(user.id)] = {}
        users[str(user.id)]['wallet'] = 0
        users[str(user.id)]['bank'] = 0 

    with open('mainbank.json', 'w') as f:
        json.dump(users,f)
    return True

async def get_bank_data():
    with open('mainbank.json', 'r') as f:
        users = json.load(f)
    return users



async def update_bank(user, change = 0, mode = 'wallet'):
    users = await get_bank_data()

    users[str(user.id)][mode] += change

    with open('mainbank.json', 'w') as f:
        json.dump(users,f)

    bal = [users[str(user.id)]['wallet'],users[str(user.id)]['bank']]
    return bal


@client.command()
async def tictactoe(ctx, p1: discord.Member, p2: discord.Member):
    global count
    global player1
    global player2
    global turn
    global gameOver

    if gameOver:
        global board
        board = [":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"]
        turn = ""
        gameOver = False
        count = 0

        player1 = p1
        player2 = p2

        # print the board
        line = ""
        for x in range(len(board)):
            if x == 2 or x == 5 or x == 8:
                line += " " + board[x]
                await ctx.send(line)
                line = ""
            else:
                line += " " + board[x]

        # determine who goes first
        num = random.randint(1, 2)
        if num == 1:
            turn = player1
            await ctx.send("It is <@" + str(player1.id) + ">'s turn.")
        elif num == 2:
            turn = player2
            await ctx.send("It is <@" + str(player2.id) + ">'s turn.")
    else:
        await ctx.send("A wise person once said that finish what you have started.")

@client.command()
async def place(ctx, pos: int):
    global turn
    global player1
    global player2
    global board
    global count
    global gameOver

    if not gameOver:
        mark = ""
        if turn == ctx.author:
            if turn == player1:
                mark = ":regional_indicator_x:"
            elif turn == player2:
                mark = ":o2:"
            if 0 < pos < 10 and board[pos - 1] == ":white_large_square:" :
                board[pos - 1] = mark
                count += 1

                # print the board
                line = ""
                for x in range(len(board)):
                    if x == 2 or x == 5 or x == 8:
                        line += " " + board[x]
                        await ctx.send(line)
                        line = ""
                    else:
                        line += " " + board[x]

                checkWinner(winningConditions, mark)
                print(count)
                if gameOver == True:
                    await ctx.send(mark + " wins!")
                elif count >= 9:
                    gameOver = True
                    await ctx.send("It's a tie!")

                # switch turns
                if turn == player1:
                    turn = player2
                elif turn == player2:
                    turn = player1
            else:
                await ctx.send("Be sure to choose an integer between 1 and 9 (inclusive) and an unmarked tile.")
        else:
            await ctx.send("It is not your turn you ||NOOB||.")
    else:
        await ctx.send("Please start a new game using the !tictactoe command.")


def checkWinner(winningConditions, mark):
    global gameOver
    for condition in winningConditions:
        if board[condition[0]] == mark and board[condition[1]] == mark and board[condition[2]] == mark:
            gameOver = True

@tictactoe.error
async def tictactoe_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Do you want to play with yourself only? Mention other people also ||NOOB||")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("With whom you wanna play? ghost? (mention like this <@688534433879556134>).")

@place.error
async def place_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Enter a position you would like to mark. ||NOOB||")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Enter a number not a letter ||Foolish||")

 

keep_alive.keep_alive()
my_secret = os.environ['SECRET']
client.run(os.environ['SECRET'])