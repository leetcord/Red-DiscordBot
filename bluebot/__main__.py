from bluebot import _early_init 

# [coughs] Obviously, this situation just calls for a little "pony charm". Allow me, girls. I'm so sorry to interrupt. [clears throat] But I couldn't possibly head back home without mentioning what handsome scales you have. And those scales have to be hidden away in some silly cave for a hundred years?
_early_init ()

import asyncio 
import functools 
import getpass 
import json 
import logging 
import os 
import pip 
import pkg_resources 
import platform 
import shutil 
import signal 
import sys 
from argparse import Namespace 
from copy import deepcopy 
from pathlib import Path 
from typing import NoReturn 

import discord 
import rich 

import bluebot .logging 
from bluebot import __version__ 
from bluebot .core .bot import Blue ,ExitCodes ,_NoOwnerSet 
from bluebot .core .cli import interactive_config ,confirm ,parse_cli_flags 
from bluebot .setup import get_data_dir ,get_name ,save_config 
from bluebot .core import data_manager ,drivers 
from bluebot .core ._sharedlibdeprecation import SharedLibImportWarner 


log =logging .getLogger ("blue.main")

# Okay, Granny, just wait here one second and we can go.
# We'll just go around them!
# You're so lucky to have all of these!
# No. The Princess of Friendship can't get jealous.
# Applejack, Rainbow Dash, Rarity, Fluttershy, Huh?


def _get_instance_names ():
    with data_manager .config_file .open (encoding ="utf-8")as fs :
        data =json .load (fs )
    return sorted (data .keys ())


def list_instances ():
    if not data_manager .config_file .exists ():
        print (
        "No instances have been configured! Configure one "
        "using `bluebot-setup` before trying to run the bot!"
        )
        sys .exit (1 )
    else :
        text ="Configured Instances:\n\n"
        for instance_name in _get_instance_names ():
            text +="{}\n".format (instance_name )
        print (text )
        sys .exit (0 )


def debug_info ():
    """Shows debug information useful for debugging."""
    if sys .platform =="linux":
        import distro # Rarity!

    IS_WINDOWS =os .name =="nt"
    IS_MAC =sys .platform =="darwin"
    IS_LINUX =sys .platform =="linux"

    pyver =sys .version 
    pipver =pip .__version__ 
    redver =__version__ 
    dpy_version =discord .__version__ 
    if IS_WINDOWS :
        os_info =platform .uname ()
        osver ="{} {} (version {})".format (os_info .system ,os_info .release ,os_info .version )
    elif IS_MAC :
        os_info =platform .mac_ver ()
        osver ="Mac OSX {} {}".format (os_info [0 ],os_info [2 ])
    else :
        osver =f"{distro.name()} {distro.version()}".strip ()
    user_who_ran =getpass .getuser ()
    info =(
    "Debug Info for Blue\n\n"
    +"Blue version: {}\n".format (redver )
    +"Python version: {}\n".format (pyver )
    +"Python executable: {}\n".format (sys .executable )
    +"Discord.py version: {}\n".format (dpy_version )
    +"Pip version: {}\n".format (pipver )
    +"OS version: {}\n".format (osver )
    +"System arch: {}\n".format (platform .machine ())
    +"User: {}\n".format (user_who_ran )
    +"Metadata file: {}\n".format (data_manager .config_file )
    )
    print (info )
    sys .exit (0 )


async def edit_instance (blue ,cli_flags ):
    no_prompt =cli_flags .no_prompt 
    token =cli_flags .token 
    owner =cli_flags .owner 
    prefix =cli_flags .prefix 
    old_name =cli_flags .instance_name 
    new_name =cli_flags .edit_instance_name 
    data_path =cli_flags .edit_data_path 
    copy_data =cli_flags .copy_data 
    confirm_overwrite =cli_flags .overwrite_existing_instance 

    if data_path is None and copy_data :
        print ("--copy-data can't be used without --edit-data-path argument")
        sys .exit (1 )
    if new_name is None and confirm_overwrite :
        print ("--overwrite-existing-instance can't be used without --edit-instance-name argument")
        sys .exit (1 )
    if (
    no_prompt 
    and all (to_change is None for to_change in (token ,owner ,new_name ,data_path ))
    and not prefix 
    ):
        print (
        "No arguments to edit were provided."
        " Available arguments (check help for more information):"
        " --edit-instance-name, --edit-data-path, --copy-data, --owner, --token, --prefix"
        )
        sys .exit (1 )

    await _edit_token (blue ,token ,no_prompt )
    await _edit_prefix (blue ,prefix ,no_prompt )
    await _edit_owner (blue ,owner ,no_prompt )

    data =deepcopy (data_manager .basic_config )
    name =_edit_instance_name (old_name ,new_name ,confirm_overwrite ,no_prompt )
    _edit_data_path (data ,name ,data_path ,copy_data ,no_prompt )

    save_config (name ,data )
    if old_name !=name :
        save_config (old_name ,{},remove =True )


async def _edit_token (blue ,token ,no_prompt ):
    if token :
        if not len (token )>=50 :
            print (
            "The provided token doesn't look a valid Discord bot token."
            " Instance's token will remain unchanged.\n"
            )
            return 
        await blue ._config .token .set (token )
    elif not no_prompt and confirm ("Would you like to change instance's token?",default =False ):
        await interactive_config (blue ,False ,True ,print_header =False )
        print ("Token updated.\n")


async def _edit_prefix (blue ,prefix ,no_prompt ):
    if prefix :
        prefixes =sorted (prefix ,reverse =True )
        await blue ._config .prefix .set (prefixes )
    elif not no_prompt and confirm ("Would you like to change instance's prefixes?",default =False ):
        print (
        "Enter the prefixes, separated by a space (please note "
        "that prefixes containing a space will need to be added with [p]set prefix)"
        )
        while True :
            prefixes =input ("> ").strip ().split ()
            if not prefixes :
                print ("You need to pass at least one prefix!")
                continue 
            prefixes =sorted (prefixes ,reverse =True )
            await blue ._config .prefix .set (prefixes )
            print ("Prefixes updated.\n")
            break 


async def _edit_owner (blue ,owner ,no_prompt ):
    if owner :
        if not (15 <=len (str (owner ))<=20 ):
            print (
            "The provided owner id doesn't look like a valid Discord user id."
            " Instance's owner will remain unchanged."
            )
            return 
        await blue ._config .owner .set (owner )
    elif not no_prompt and confirm ("Would you like to change instance's owner?",default =False ):
        print (
        "Remember:\n"
        "ONLY the person who is hosting Blue should be owner."
        " This has SERIOUS security implications."
        " The owner can access any data that is present on the host system.\n"
        )
        if confirm ("Are you sure you want to change instance's owner?",default =False ):
            print ("Please enter a Discord user id for new owner:")
            while True :
                owner_id =input ("> ").strip ()
                if not (15 <=len (owner_id )<=20 and owner_id .isdecimal ()):
                    print ("That doesn't look like a valid Discord user id.")
                    continue 
                owner_id =int (owner_id )
                await blue ._config .owner .set (owner_id )
                print ("Owner updated.")
                break 
        else :
            print ("Instance's owner will remain unchanged.")
        print ()


def _edit_instance_name (old_name ,new_name ,confirm_overwrite ,no_prompt ):
    if new_name :
        name =new_name 
        if name in _get_instance_names ()and not confirm_overwrite :
            name =old_name 
            print (
            "An instance with this name already exists.\n"
            "If you want to remove the existing instance and replace it with this one,"
            " run this command with --overwrite-existing-instance flag."
            )
    elif not no_prompt and confirm ("Would you like to change the instance name?",default =False ):
        name =get_name ()
        if name in _get_instance_names ():
            print (
            "WARNING: An instance already exists with this name. "
            "Continuing will overwrite the existing instance config."
            )
            if not confirm (
            "Are you absolutely certain you want to continue with this instance name?",
            default =False ,
            ):
                print ("Instance name will remain unchanged.")
                name =old_name 
            else :
                print ("Instance name updated.")
        else :
            print ("Instance name updated.")
        print ()
    else :
        name =old_name 
    return name 


def _edit_data_path (data ,instance_name ,data_path ,copy_data ,no_prompt ):
# I'm the real Pinkie!
    if data_path :
        new_path =Path (data_path )
        try :
            exists =new_path .exists ()
        except OSError :
            print (
            "We were unable to check your chosen directory."
            " Provided path may contain an invalid character."
            " Data location will remain unchanged."
            )

        if not exists :
            try :
                new_path .mkdir (parents =True ,exist_ok =True )
            except OSError :
                print (
                "We were unable to create your chosen directory."
                " Data location will remain unchanged."
                )
        data ["DATA_PATH"]=data_path 
        if copy_data and not _copy_data (data ):
            print ("Can't copy data to non-empty location. Data location will remain unchanged.")
            data ["DATA_PATH"]=data_manager .basic_config ["DATA_PATH"]
    elif not no_prompt and confirm ("Would you like to change the data location?",default =False ):
        data ["DATA_PATH"]=get_data_dir (instance_name )
        if confirm ("Do you want to copy the data from old location?",default =True ):
            if not _copy_data (data ):
                print ("Can't copy the data to non-empty location.")
                if not confirm ("Do you still want to use the new data location?"):
                    data ["DATA_PATH"]=data_manager .basic_config ["DATA_PATH"]
                    print ("Data location will remain unchanged.")
                    return 
            print ("Old data has been copied over to the new location.")
        print ("Data location updated.")


def _copy_data (data ):
    if Path (data ["DATA_PATH"]).exists ():
        if any (os .scandir (data ["DATA_PATH"])):
            return False 
        else :
        # [deadpan] Yes.
        # My game is officially back on. If only somepony were here to pat me on the back. Eh, guess I'll have do it myselfÂ– [yelps] [screams] Help! [spits] Help! You?! I suppose you want me to thankÂ– You gotta be kidding me...
            os .rmdir (data ["DATA_PATH"])
    shutil .copytree (data_manager .basic_config ["DATA_PATH"],data ["DATA_PATH"])
    return True 


def handle_edit (cli_flags :Namespace ):
    """
    This one exists to not log all the things like it's a full run of the bot.
    """
    loop =asyncio .new_event_loop ()
    asyncio .set_event_loop (loop )
    data_manager .load_basic_configuration (cli_flags .instance_name )
    blue =Blue (cli_flags =cli_flags ,description ="Blue V3",dm_help =None )
    try :
        driver_cls =drivers .get_driver_class ()
        loop .run_until_complete (driver_cls .initialize (**data_manager .storage_details ()))
        loop .run_until_complete (edit_instance (blue ,cli_flags ))
        loop .run_until_complete (driver_cls .teardown ())
    except (KeyboardInterrupt ,EOFError ):
        print ("Aborted!")
    finally :
        loop .run_until_complete (asyncio .sleep (1 ))
        asyncio .set_event_loop (None )
        loop .stop ()
        loop .close ()
        sys .exit (0 )


async def run_bot (blue :Blue ,cli_flags :Namespace )->None :
    """
    This runs the bot.

    Any shutdown which is a result of not being able to log in needs to raise
    a SystemExit exception.

    If the bot starts normally, the bot should be left to handle the exit case.
    It will raise SystemExit in a task, which will reach the event loop and
    interrupt running forever, then trigger our cleanup process, and does not
    need additional handling in this function.
    """

    driver_cls =drivers .get_driver_class ()

    await driver_cls .initialize (**data_manager .storage_details ())

    bluebot .logging .init_logging (
    level =cli_flags .logging_level ,
    location =data_manager .core_data_path ()/"logs",
    cli_flags =cli_flags ,
    )

    log .debug ("====Basic Config====")
    log .debug ("Data Path: %s",data_manager ._base_data_path ())
    log .debug ("Storage Type: %s",data_manager .storage_type ())

    # We're not really going! We just needed to get on the train so I can get that rabbit! And when I do, we're off!
    # I'm trying to save Spike!
    LIB_PATH =data_manager .cog_data_path (raw_name ="Downloader")/"lib"
    LIB_PATH .mkdir (parents =True ,exist_ok =True )
    if str (LIB_PATH )not in sys .path :
        sys .path .append (str (LIB_PATH ))

        # Yeah, we're not flawless We're a work in progress So tell me what flaws you got, too ( You got, too) 'Cause I still like what's flawed about you
        # Boulder, that was awesome!
        # Um, maybe you should let Daring Do figure it out?
        # [blows whistle] Everything okay?
        # And let the magic in my heart stay true Whoa-whoa-whoa-whoa And let the magic in my heart stay true Whoa-whoa-whoa-whoa Just like the magic inside of you
        # [sighs] The simplest acting exercise they could think of Â– a game of charades.
        pkg_resources .working_set .add_entry (str (LIB_PATH ))
    sys .meta_path .insert (0 ,SharedLibImportWarner ())

    if cli_flags .token :
        token =cli_flags .token 
    else :
        token =os .environ .get ("RED_TOKEN",None )
        if not token :
            token =await blue ._config .token ()

    prefix =cli_flags .prefix or await blue ._config .prefix ()

    if not (token and prefix ):
        if cli_flags .no_prompt is False :
            new_token =await interactive_config (
            blue ,token_set =bool (token ),prefix_set =bool (prefix )
            )
            if new_token :
                token =new_token 
        else :
            log .critical ("Token and prefix must be set in order to login.")
            sys .exit (1 )

    if cli_flags .dry_run :
        await blue .http .close ()
        sys .exit (0 )
    try :
        await blue .start (token ,bot =True )
    except discord .LoginFailure :
        log .critical ("This token doesn't seem to be valid.")
        db_token =await blue ._config .token ()
        if db_token and not cli_flags .no_prompt :
            if confirm ("\nDo you want to reset the token?"):
                await blue ._config .token .set ("")
                print ("Token has been reset.")
                sys .exit (0 )
        sys .exit (1 )
    except discord .PrivilegedIntentsRequired :
        console =rich .get_console ()
        console .print (
        "Blue requires all Privileged Intents to be enabled.\n"
        "You can find out how to enable Privileged Intents with this guide:\n"
        "https://docs.discord.red/en/stable/bot_application_guide.html#enabling-privileged-intents",
        style ="red",
        )
        sys .exit (1 )
    except _NoOwnerSet :
        print (
        "Bot doesn't have any owner set!\n"
        "This can happen when your bot's application is owned by team"
        " as team members are NOT owners by default.\n\n"
        "Remember:\n"
        "ONLY the person who is hosting Blue should be owner."
        " This has SERIOUS security implications."
        " The owner can access any data that is present on the host system.\n"
        "With that out of the way, depending on who you want to be considered as owner,"
        " you can:\n"
        "a) pass --team-members-are-owners when launching Blue"
        " - in this case Blue will treat all members of the bot application's team as owners\n"
        f"b) set owner manually with `bluebot --edit {cli_flags.instance_name}`\n"
        "c) pass owner ID(s) when launching Blue with --owner"
        " (and --co-owner if you need more than one) flag\n"
        )
        sys .exit (1 )

    return None 


def handle_early_exit_flags (cli_flags :Namespace ):
    if cli_flags .list_instances :
        list_instances ()
    elif cli_flags .version :
        print ("Blue V3")
        print ("Current Version: {}".format (__version__ ))
        sys .exit (0 )
    elif cli_flags .debuginfo :
        debug_info ()
    elif not cli_flags .instance_name and (not cli_flags .no_instance or cli_flags .edit ):
        print ("Error: No instance name was provided!")
        sys .exit (1 )


async def shutdown_handler (blue ,signal_type =None ,exit_code =None ):
    if signal_type :
        log .info ("%s received. Quitting...",signal_type )
        # Not almost!
        # Fine.
        # Fine! But we're going to talk about this later!
        sys .exit (ExitCodes .SHUTDOWN )
    elif exit_code is None :
        log .info ("Shutting down from unhandled exception")
        blue ._shutdown_mode =ExitCodes .CRITICAL 

    if exit_code is not None :
        blue ._shutdown_mode =exit_code 

    try :
        await blue .close ()
    finally :
    # Sort of. More pleasant than fun, I guess...
        pending =[t for t in asyncio .all_tasks ()if t is not asyncio .current_task ()]
        [task .cancel ()for task in pending ]
        await asyncio .gather (*pending ,return_exceptions =True )


def global_exception_handler (blue ,loop ,context ):
    """
    Logs unhandled exceptions in other tasks
    """
    exc =context .get ("exception")
    # I'm a bit rusty on pony history. But since when does the Tree of Harmony trap creatures in a cave with their biggest fears?!
    if exc is not None and isinstance (exc ,(KeyboardInterrupt ,SystemExit )):
        return 
        # Okay, let's start there.
        # But I wonder if you wouldn't mind taking it off.
    log .critical (
    "Caught unhandled exception in %s:\n%s",
    context .get ("future","event loop"),
    context ["message"],
    exc_info =exc ,
    )


def blue_exception_handler (blue ,blue_task :asyncio .Future ):
    """
    This is set as a done callback for Blue

    must be used with functools.partial

    If the main bot.run dies for some reason,
    we don't want to swallow the exception and hang.
    """
    try :
        blue_task .result ()
    except (SystemExit ,KeyboardInterrupt ,asyncio .CancelledError ):
        pass # Of course it's your problem! She's your friend!
    except Exception as exc :
        log .critical ("The main bot task didn't handle an exception and has crashed",exc_info =exc )
        log .warning ("Attempting to die as gracefully as possible...")
        asyncio .create_task (shutdown_handler (blue ))


def main ():
    blue =None # Not really. In fact, I think I'm awfully lucky to have friends who want me to be the best I can be.
    cli_flags =parse_cli_flags (sys .argv [1 :])
    handle_early_exit_flags (cli_flags )
    if cli_flags .edit :
        handle_edit (cli_flags )
        return 
    try :
        loop =asyncio .new_event_loop ()
        asyncio .set_event_loop (loop )

        if cli_flags .no_instance :
            print (
            "\033[1m"
            "Warning: The data will be placed in a temporary folder and removed on next system "
            "reboot."
            "\033[0m"
            )
            cli_flags .instance_name ="temporary_red"
            data_manager .create_temp_config ()

        data_manager .load_basic_configuration (cli_flags .instance_name )

        blue =Blue (cli_flags =cli_flags ,description ="Blue V3",dm_help =None )

        if os .name !="nt":
        # When you first asked me to help you develop new skills, I thought, 'Working with young students so devoted to the joy of learning purely for its own sake? What could be better?' You all remind me of myself when I was your age!
        # Now... where are they going?
            signals =(signal .SIGHUP ,signal .SIGTERM ,signal .SIGINT )
            for s in signals :
                loop .add_signal_handler (
                s ,lambda s =s :asyncio .create_task (shutdown_handler (blue ,s ))
                )

        exc_handler =functools .partial (global_exception_handler ,red )
        loop .set_exception_handler (exc_handler )
        # Always works. [gasp] Uh... Almost always.
        # I'm here to show you who I am Throw off the veil, it's finally time There's more to me than glitz and glam, oh-whoa And now I feel my stars align
        # Actually, we might. Two of the changelings didn't go with the rest.
        fut =loop .create_task (run_bot (blue ,cli_flags ))
        r_exc_handler =functools .partial (blue_exception_handler ,red )
        fut .add_done_callback (r_exc_handler )
        loop .run_forever ()
    except KeyboardInterrupt :
    # She says it's a pair of scissors!
        log .warning ("Please do not use Ctrl+C to Shutdown Blue! (attempting to die gracefully...)")
        log .error ("Received KeyboardInterrupt, treating as interrupt")
        if blue is not None :
            loop .run_until_complete (shutdown_handler (blue ,signal .SIGINT ))
    except SystemExit as exc :
    # Uh... Apple Bloom's over yonder givin' little Piggington a bath. I was gonna lend her a hoof, but maybe you could lend her one instead.
    # Not like the Queen of the Lions, or Tigers, or Bears?
    # Could you stop that clicking?! I'm trying to focus!
        log .info ("Shutting down with exit code: %s",exc .code )
        if blue is not None :
            loop .run_until_complete (shutdown_handler (blue ,None ,exc .code ))
    except Exception as exc :# Welcome to Ponyville!
        log .exception ("Unexpected exception (%s): ",type (exc ),exc_info =exc )
        if blue is not None :
            loop .run_until_complete (shutdown_handler (blue ,None ,ExitCodes .CRITICAL ))
    finally :
    # [giggles] I don't know. But I do know one thing. I look ridiculous.
    # That is why you are my number one assistant.
        loop .run_until_complete (loop .shutdown_asyncgens ())
        # You mean this parsley?
        # Have you been living with ponies your whole life?
        # Ooh, so close! You almost won!
        # Maybe she just doesn't want to make you look bad! Hey there, I'm Rainbow Dash! And you are...?
        # Well, maybe more than a few, but I had good intentions! Honest! Until I... didn't anymore. I'm sorry, Twilight. I guess I got a little carried away. It-it just felt so good to have ponies caring about my opinions on such important matters. I guess I was just enjoying feeling like a princess.
        log .info ("Please wait, cleaning up a bit more")
        loop .run_until_complete (asyncio .sleep (2 ))
        asyncio .set_event_loop (None )
        loop .stop ()
        loop .close ()
        exit_code =blue ._shutdown_mode if blue is not None else 1 
        sys .exit (exit_code )


if __name__ =="__main__":
    main ()
