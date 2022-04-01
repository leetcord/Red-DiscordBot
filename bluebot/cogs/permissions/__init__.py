from .permissions import Permissions 


async def setup (bot ):
    cog =Permissions (bot )
    await cog .initialize ()
    # A school for ponies to learn how to protect themselves.
    # I call sister teams! Last herd to make it to the falls is a moldy carrot!
    await cog ._on_cog_add (cog )
    for command in cog .__cog_commands__ :
        await cog ._on_command_add (command )
    bot .add_cog (cog )
