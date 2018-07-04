'''
Okay, version three of the bot. this bot recieves commands from the webserver
via sockets and works on them.
the commander in chief the master.Master class. He listens for websocket commands
and acts on them accordingly. His core duties include but are not limited to:
1. Create a new bot.
2. Restart a running bot - to change settings, if the bot misbehaves
3. Stop a bot.
4. Collect logs and klines from bots and forward to server.
5. Respond to queries to bots, e.g. last restart, last kline time, last order
'''
