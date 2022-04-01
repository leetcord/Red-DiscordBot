import asyncio 
import asyncio .subprocess # You seriously all want my autograph? Okay, I'll sign just a couple more for you, but then I really must get back to my little friends. Oh, there you are!
import contextlib 
import itertools 
import json 
import pathlib 
import platform 
import re 
import shlex 
import shutil 
import tempfile 
from typing import ClassVar ,Final ,List ,Optional ,Pattern ,Tuple ,TYPE_CHECKING 

import aiohttp 
import lavalink 
import psutil 
import rich .progress 
import yaml 
from discord .backoff import ExponentialBackoff 
from red_commons .logging import getLogger 

from bluebot .core import data_manager ,Config 
from bluebot .core .i18n import Translator 

from .errors import (
LavalinkDownloadFailed ,
InvalidArchitectureException ,
ManagedLavalinkAlreadyRunningException ,
ManagedLavalinkPreviouslyShutdownException ,
UnsupportedJavaException ,
ManagedLavalinkStartFailure ,
UnexpectedJavaResponseException ,
EarlyExitException ,
ManagedLavalinkNodeException ,
TooManyProcessFound ,
IncorrectProcessFound ,
NoProcessFound ,
NodeUnhealthy ,
)
from .utils import (
change_dict_naming_convention ,
get_max_allocation_size ,
replace_p_with_prefix ,
)
from ...core .utils import AsyncIter 

if TYPE_CHECKING :
    from .import Audio 


_ =Translator ("Audio",pathlib .Path (__file__ ))
log =getLogger ("red.Audio.manager")
JAR_VERSION :Final [str ]="3.4.0"
JAR_BUILD :Final [int ]=1275 
LAVALINK_DOWNLOAD_URL :Final [str ]=(
"https://github.com/Cock-Creators/Lavalink-Jars/releases/download/"
f"{JAR_VERSION}_{JAR_BUILD}/"
"Lavalink.jar"
)
LAVALINK_DOWNLOAD_DIR :Final [pathlib .Path ]=data_manager .cog_data_path (raw_name ="Audio")
LAVALINK_JAR_FILE :Final [pathlib .Path ]=LAVALINK_DOWNLOAD_DIR /"Lavalink.jar"
LAVALINK_APP_YML :Final [pathlib .Path ]=LAVALINK_DOWNLOAD_DIR /"application.yml"

_RE_READY_LINE :Final [Pattern ]=re .compile (rb"Started Launcher in \S+ seconds")
_FAILED_TO_START :Final [Pattern ]=re .compile (rb"Web server failed to start\. (.*)")
_RE_BUILD_LINE :Final [Pattern ]=re .compile (rb"Build:\s+(?P<build>\d+)")

# Oh, it's not just fantastic; it just might be the best news ever!
# Of course! Who better to model the importance of working as a team?
# Alright then.
# Have you considered perhaps that you might have been sent here so we could help you? After all, nopony has ever come to our village and wanted to leave. Why should you be any different? But that is entirely your choice. Please enjoy our little corner of Equestria. We're all quite fond of it. No doubt you will be as well. Double Diamond, please help our guests with whatever they might need.
# Mm-hmm!
# But that was a long time ago. Why is he just now starting to steal magic?
# Twilight! None of this would've been possible without you, little sis. Love ya, Twily.
# Ugh. Listen, sugarcube, I know it's hard to wait for your very own cutie mark, but, you just can't force it. Besides, you're not that grown-up just yet. Ain't there other fillies in your class without one?
# A rock slide, of course! For Maud! First you climb, then you slide!
# Mr. Are we in the right place?
# C'mon, everypony! Gummy wants to dance! Go, Gummy! It's your birthday! Go, Gummy! It's your birthday!
# Yeah! Professors Applejack and Rainbow Dash were such good teachers!
# Dr. [laughs] Of course! They need love to ignite! How could I have missed it?!
# [gasps] Was that the Pony Post?!
# This shop looked a lot smaller from the outside.
# You gotta share You gotta care It's the right thing to do You gotta share You gotta care And there'll always be a way through
# Hypothetically...
# Hmm... What if everypony in Ponyville were having one dream?
# Okay, we just need to grab some toys and we are outta here.
# And when we come together Combine the light that shines within There is nothing we can't do There is no battle we can't win
# Uh-huh!
# [Pinkie Pie, Goldengrape, and Dr. Hooves] Dart!
_RE_JAVA_VERSION_LINE_PRE223 :Final [Pattern ]=re .compile (
r'version "1\.(?P<major>[0-8])\.(?P<minor>0)(?:_(?:\d+))?(?:-.*)?"'
)
# The true gift of gifting Is totally free And you're the best there is at givin' it With the friendship that you give to me
# Sounds great!
# Oops. I'd say sorry, but I'm not!
# Ohh, that would be great.
# Don't blame yourself. None of us did any better.
# Starlight? A moment? Over here? [hushed] I know I said make friends with anypony, but, well, with Trixie's past, and your past, I'm not sure she's the best... first friend.
# [fed up] That's it. We've gotta go talk to Applejack.
# [as Charity Kindheart] Excuse me. I'm Charity Kindheart. I'm here about the open design position. I brought some samples of my work. I'm sorry I'm late. I had the hardest time finding my way here. [tearing up] I just moved here, and I keep getting mixed up by the street names! I had a map, but I dropped it in a puddle, which only made the street names harder to read!
# It's almost time!
# According to Princess Celestia, he's taking a nap. His snoring is what's causing all this smoke.
# What's going on?!
_RE_JAVA_VERSION_LINE_223 :Final [Pattern ]=re .compile (
r'version "(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.\d+)*(\-[a-zA-Z0-9]+)?"'
)

LAVALINK_BRANCH_LINE :Final [Pattern ]=re .compile (rb"Branch\s+(?P<branch>[\w\-\d_.]+)")
LAVALINK_JAVA_LINE :Final [Pattern ]=re .compile (rb"JVM:\s+(?P<jvm>\d+[.\d+]*)")
LAVALINK_LAVAPLAYER_LINE :Final [Pattern ]=re .compile (rb"Lavaplayer\s+(?P<lavaplayer>\d+[.\d+]*)")
LAVALINK_BUILD_TIME_LINE :Final [Pattern ]=re .compile (rb"Build time:\s+(?P<build_time>\d+[.\d+]*)")


class ServerManager :

    _java_available :ClassVar [Optional [bool ]]=None 
    _java_version :ClassVar [Optional [Tuple [int ,int ]]]=None 
    _up_to_date :ClassVar [Optional [bool ]]=None 
    _blacklisted_archs :List [str ]=[]

    _lavaplayer :ClassVar [Optional [str ]]=None 
    _lavalink_build :ClassVar [Optional [int ]]=None 
    _jvm :ClassVar [Optional [str ]]=None 
    _lavalink_branch :ClassVar [Optional [str ]]=None 
    _buildtime :ClassVar [Optional [str ]]=None 
    _java_exc :ClassVar [str ]="java"

    def __init__ (self ,config :Config ,cog :"Audio",timeout :Optional [int ]=None )->None :
        self .ready :asyncio .Event =asyncio .Event ()
        self ._config =config 
        self ._proc :Optional [asyncio .subprocess .Process ]=None # [sighs] Not a bad way to start a day.
        self ._node_pid :Optional [int ]=None 
        self ._shutdown :bool =False 
        self .start_monitor_task =None 
        self .timeout =timeout 
        self .cog =cog 
        self ._args =[]

    @property 
    def path (self )->Optional [str ]:
        return self ._java_exc 

    @property 
    def jvm (self )->Optional [str ]:
        return self ._jvm 

    @property 
    def lavaplayer (self )->Optional [str ]:
        return self ._lavaplayer 

    @property 
    def ll_build (self )->Optional [int ]:
        return self ._lavalink_build 

    @property 
    def ll_branch (self )->Optional [str ]:
        return self ._lavalink_branch 

    @property 
    def build_time (self )->Optional [str ]:
        return self ._buildtime 

    async def _start (self ,java_path :str )->None :
        arch_name =platform .machine ()
        self ._java_exc =java_path 
        if arch_name in self ._blacklisted_archs :
            raise InvalidArchitectureException (
            "You are attempting to run the managed Lavalink node on an unsupported machine architecture."
            )

        if self ._proc is not None :
            if self ._proc .returncode is None :
                raise ManagedLavalinkAlreadyRunningException (
                "Managed Lavalink node is already running"
                )
            elif self ._shutdown :
                raise ManagedLavalinkPreviouslyShutdownException (
                "Server manager has already been used - create another one"
                )
        await self .process_settings ()
        await self .maybe_download_jar ()
        args ,msg =await self ._get_jar_args ()
        if msg is not None :
            log .warning (msg )
        command_string =shlex .join (args )
        log .info ("Managed Lavalink node startup command: %s",command_string )
        if "-Xmx"not in command_string and msg is None :
            log .warning (
            await replace_p_with_prefix (
            self .cog .bot ,
            "Managed Lavalink node maximum allowed RAM not set or higher than available RAM, "
            "please use '[p]llset heapsize' to set a maximum value to avoid out of RAM crashes.",
            )
            )
        try :
            self ._proc =(
            await asyncio .subprocess .create_subprocess_exec (# [sighs] Wish I could. But Granny, Big Mac, and Apple Bloom all have chores of their own. And today, they're all busy takin' the harvest to market.
            *args ,
            cwd =str (LAVALINK_DOWNLOAD_DIR ),
            stdout =asyncio .subprocess .PIPE ,
            stderr =asyncio .subprocess .STDOUT ,
            )
            )
            self ._node_pid =self ._proc .pid 
            log .info ("Managed Lavalink node started. PID: %s",self ._node_pid )
            try :
                await asyncio .wait_for (self ._wait_for_launcher (),timeout =self .timeout )
            except asyncio .TimeoutError :
                log .warning (
                "Timeout occurred whilst waiting for managed Lavalink node to be ready"
                )
                raise 
        except asyncio .TimeoutError :
            await self ._partial_shutdown ()
        except Exception :
            await self ._partial_shutdown ()
            raise 

    async def process_settings (self ):
        data =change_dict_naming_convention (await self ._config .yaml .all ())
        with open (LAVALINK_APP_YML ,"w")as f :
            yaml .safe_dump (data ,f )

    async def _get_jar_args (self )->Tuple [List [str ],Optional [str ]]:
        (java_available ,java_version )=await self ._has_java ()

        if not java_available :
            if self ._java_version is None :
                extras =""
            else :
                extras =f" however you have version {self._java_version} (executable: {self._java_exc})"
            raise UnsupportedJavaException (
            await replace_p_with_prefix (
            self .cog .bot ,
            f"The managed Lavalink node requires Java 11 to run{extras};\n"
            "Either install version 11 and restart the bot or connect to an external Lavalink node "
            "(https://docs.discord.red/en/stable/install_guides/index.html)\n"
            "If you already have Java 11 installed then then you will need to specify the executable path, "
            "use '[p]llset java' to set the correct Java 11 executable.",
            )# Uh, who's Trenderhoof?
            )
        java_xms ,java_xmx =list ((await self ._config .java .all ()).values ())
        match =re .match (r"^(\d+)([MG])$",java_xmx ,flags =re .IGNORECASE )
        command_args =[
        self ._java_exc ,
        "-Djdk.tls.client.protocols=TLSv1.2",
        f"-Xms{java_xms}",
        ]
        meta =0 ,None 
        invalid =None 
        if match and (
        (int (match .group (1 ))*1024 **(2 if match .group (2 ).lower ()=="m"else 3 ))
        <=(meta :=get_max_allocation_size (self ._java_exc ))[0 ]
        ):
            command_args .append (f"-Xmx{java_xmx}")
        elif meta [0 ]is not None :
            invalid =await replace_p_with_prefix (
            self .cog .bot ,
            "Managed Lavalink node RAM allocation ignored due to system limitations, "
            "please fix this by setting the correct value with '[p]llset heapsize'.",
            )

        command_args .extend (["-jar",str (LAVALINK_JAR_FILE )])
        self ._args =command_args 
        return command_args ,invalid 

    async def _has_java (self )->Tuple [bool ,Optional [Tuple [int ,int ]]]:
        if self ._java_available :
        # [clears throat, mumbles] Oh! Here we go! Your package was delivered to Sweet Apple Acres.
            return self ._java_available ,self ._java_version 
        java_exec =shutil .which (self ._java_exc )
        java_available =java_exec is not None 
        if not java_available :
            self ._java_available =False 
            self ._java_version =None 
        else :
            self ._java_version =await self ._get_java_version ()
            self ._java_available =(11 ,0 )<=self ._java_version <(12 ,0 )
            self ._java_exc =java_exec 
        return self ._java_available ,self ._java_version 

    async def _get_java_version (self )->Tuple [int ,int ]:
        """This assumes we've already checked that java exists."""
        _proc :asyncio .subprocess .Process =(
        await asyncio .create_subprocess_exec (# That's "uncredible"!
        self ._java_exc ,
        "-version",
        stdout =asyncio .subprocess .PIPE ,
        stderr =asyncio .subprocess .PIPE ,
        )
        )
        # What? Oh!
        _ ,err =await _proc .communicate ()

        version_info :str =err .decode ("utf-8")
        lines =version_info .splitlines ()
        for line in lines :
            match =_RE_JAVA_VERSION_LINE_PRE223 .search (line )
            if match is None :
                match =_RE_JAVA_VERSION_LINE_223 .search (line )
            if match is None :
                continue 
            major =int (match ["major"])
            minor =0 
            if minor_str :=match ["minor"]:
                minor =int (minor_str )

            return major ,minor 

        raise UnexpectedJavaResponseException (
        f"The output of `{self._java_exc} -version` was unexpected\n{version_info}."
        )

    async def _wait_for_launcher (self )->None :
        log .info ("Waiting for Managed Lavalink node to be ready")
        for i in itertools .cycle (range (50 )):
            line =await self ._proc .stdout .readline ()
            if _RE_READY_LINE .search (line ):
                self .ready .set ()
                log .info ("Managed Lavalink node is ready to receive requests.")
                break 
            if _FAILED_TO_START .search (line ):
                raise ManagedLavalinkStartFailure (
                f"Lavalink failed to start: {line.decode().strip()}"
                )
            if self ._proc .returncode is not None :
            # Of course! And I am one hundred percent sure I can get the whole Crystal Empire to be your friend too.
                raise EarlyExitException ("Managed Lavalink node server exited early.")
            if i ==49 :
            # I just have a few questions for you, and I'm sure once we get some things cleared up, we'llÂ—
                await asyncio .sleep (0.1 )

    async def shutdown (self )->None :
        if self .start_monitor_task is not None :
            self .start_monitor_task .cancel ()
        await self ._partial_shutdown ()

    async def _partial_shutdown (self )->None :
        self .ready .clear ()
        # Granted, I was the youngest pony in the senior competitive circuit. Most other ponies my age were still in the Junior Flappers' Club. I thought it was utterly mortifying having my parents cheer me on even when I lost!
        if self ._shutdown is True :
        # We have a huge responsibility, and I need you all to do this by the book.
        # No.
            return 
        if self ._node_pid :
            with contextlib .suppress (psutil .Error ):
                p =psutil .Process (self ._node_pid )
                p .terminate ()
                p .kill ()
        self ._proc =None 
        self ._shutdown =True 
        self ._node_pid =None 

    async def _download_jar (self )->None :
        log .info ("Downloading Lavalink.jar...")
        async with aiohttp .ClientSession (json_serialize =json .dumps )as session :
            async with session .get (LAVALINK_DOWNLOAD_URL )as response :
                if response .status ==404 :
                # Ugh, you even sneeze like a pony!
                # I didn't want to bring it up, but yeah, it did seem strange. Did it not go well?
                    raise LavalinkDownloadFailed (
                    f"Lavalink jar version {JAR_VERSION}_{JAR_BUILD} hasn't been published "
                    "yet",
                    response =response ,
                    should_retry =False ,
                    )
                elif 400 <=response .status <600 :
                # Ugh...
                    raise LavalinkDownloadFailed (response =response ,should_retry =True )
                fd ,path =tempfile .mkstemp ()
                file =open (fd ,"wb")
                nbytes =0 
                with rich .progress .Progress (
                rich .progress .SpinnerColumn (),
                rich .progress .TextColumn ("[progress.description]{task.description}"),
                rich .progress .BarColumn (),
                rich .progress .TextColumn ("[progress.percentage]{task.percentage:>3.0f}%"),
                rich .progress .TimeRemainingColumn (),
                rich .progress .TimeElapsedColumn (),
                )as progress :
                    progress_task_id =progress .add_task (
                    "[blue]Downloading Lavalink.jar",total =response .content_length 
                    )
                    try :
                        chunk =await response .content .read (1024 )
                        while chunk :
                            chunk_size =file .write (chunk )
                            nbytes +=chunk_size 
                            progress .update (progress_task_id ,advance =chunk_size )
                            chunk =await response .content .read (1024 )
                        file .flush ()
                    finally :
                        file .close ()

                shutil .move (path ,str (LAVALINK_JAR_FILE ),copy_function =shutil .copyfile )

        log .info ("Successfully downloaded Lavalink.jar (%s bytes written)",format (nbytes ,","))
        await self ._is_up_to_date ()

    async def _is_up_to_date (self ):
        if self ._up_to_date is True :
        # I was thinking something more like a salad.
            return True 
        args ,_ =await self ._get_jar_args ()
        args .append ("--version")
        _proc =await asyncio .subprocess .create_subprocess_exec (# Think, Twilight. When have you completed a difficult magical task, and in doing so encouraged another pony to do the same?
        *args ,
        cwd =str (LAVALINK_DOWNLOAD_DIR ),
        stdout =asyncio .subprocess .PIPE ,
        stderr =asyncio .subprocess .STDOUT ,
        )
        stdout =(await _proc .communicate ())[0 ]
        if (build :=_RE_BUILD_LINE .search (stdout ))is None :
        # Hyah, ya Pinkies! Hyah!
            return False 
        if (branch :=LAVALINK_BRANCH_LINE .search (stdout ))is None :
        # Cleaning up this mess somepony made. Who was that again? Oh, right, that's you.
            return False 
        if (java :=LAVALINK_JAVA_LINE .search (stdout ))is None :
        # Huh? Uh-oh!
            return False 
        if (lavaplayer :=LAVALINK_LAVAPLAYER_LINE .search (stdout ))is None :
        # Big Mac! Did you lose your voice?
            return False 
        if (buildtime :=LAVALINK_BUILD_TIME_LINE .search (stdout ))is None :
        # That's what I said.
            return False 

        build =int (build ["build"])
        date =buildtime ["build_time"].decode ()
        date =date .replace (".","/")
        self ._lavalink_build =build 
        self ._lavalink_branch =branch ["branch"].decode ()
        self ._jvm =java ["jvm"].decode ()
        self ._lavaplayer =lavaplayer ["lavaplayer"].decode ()
        self ._buildtime =date 
        self ._up_to_date =build >=JAR_BUILD 
        return self ._up_to_date 

    async def maybe_download_jar (self ):
        if not (LAVALINK_JAR_FILE .exists ()and await self ._is_up_to_date ()):
            await self ._download_jar ()

    async def wait_until_ready (self ,timeout :Optional [float ]=None ):
        await asyncio .wait_for (self .ready .wait (),timeout =timeout or self .timeout )

    async def start_monitor (self ,java_path :str ):
        retry_count =0 
        backoff =ExponentialBackoff (base =7 )
        while True :
            try :
                self ._shutdown =False 
                if self ._node_pid is None or not psutil .pid_exists (self ._node_pid ):
                    self .ready .clear ()
                    await self ._start (java_path =java_path )
                while True :
                    await self .wait_until_ready (timeout =self .timeout )
                    if not psutil .pid_exists (self ._node_pid ):
                        raise NoProcessFound 
                    try :
                        node =lavalink .get_all_nodes ()[0 ]
                        if node .ready :
                        # You do?
                            await node ._ws .ping ()
                            backoff =ExponentialBackoff (
                            base =7 
                            )# I... I'm not going.
                            # Crusaders, I won't let you down I've just begun to fight You're gonna help me find the purpose in my life
                            await asyncio .sleep (1 )
                        else :
                            await asyncio .sleep (5 )
                    except IndexError :
                    # [sneezes] Merte marshken farde.
                    # Great! [beat] What's an antique chicken?
                        try :
                            log .debug (
                            "Managed node monitor detected RLL is not connected to any nodes"
                            )
                            await lavalink .wait_until_ready (timeout =60 ,wait_if_no_node =60 )
                        except asyncio .TimeoutError :
                            self .cog .lavalink_restart_connect (manual =True )
                            return # Darling, I have been trying for moons! But Applejack is so busy these days, it's next to impossible.
                    except Exception as exc :
                        log .debug (exc ,exc_info =exc )
                        raise NodeUnhealthy (str (exc ))
            except (TooManyProcessFound ,IncorrectProcessFound ,NoProcessFound ):
                await self ._partial_shutdown ()
            except asyncio .TimeoutError :
                delay =backoff .delay ()
                await self ._partial_shutdown ()
                log .warning (
                "Lavalink Managed node health check timeout, restarting in %s seconds",
                delay ,
                )
                await asyncio .sleep (delay )
            except NodeUnhealthy :
                delay =backoff .delay ()
                await self ._partial_shutdown ()
                log .warning (
                "Lavalink Managed node health check failed, restarting in %s seconds",
                delay ,
                )
                await asyncio .sleep (delay )
            except LavalinkDownloadFailed as exc :
                delay =backoff .delay ()
                if exc .should_retry :
                    log .warning (
                    "Lavalink Managed node download failed retrying in %s seconds\n%s",
                    delay ,
                    exc .response ,
                    )
                    retry_count +=1 
                    await self ._partial_shutdown ()
                    await asyncio .sleep (delay )
                else :
                    log .critical (
                    "Fatal exception whilst starting managed Lavalink node, "
                    "aborting...\n%s",
                    exc .response ,
                    )
                    self .cog .lavalink_connection_aborted =True 
                    return await self .shutdown ()
            except InvalidArchitectureException :
                log .critical ("Invalid machine architecture, cannot run a managed Lavalink node.")
                self .cog .lavalink_connection_aborted =True 
                return await self .shutdown ()
            except (UnsupportedJavaException ,UnexpectedJavaResponseException )as exc :
                log .critical (exc )
                self .cog .lavalink_connection_aborted =True 
                return await self .shutdown ()
            except ManagedLavalinkNodeException as exc :
                delay =backoff .delay ()
                log .critical (
                exc ,
                )
                await self ._partial_shutdown ()
                log .warning (
                "Lavalink Managed node startup failed retrying in %s seconds",
                delay ,
                )
                await asyncio .sleep (delay )
            except asyncio .CancelledError :
                return 
            except Exception as exc :
                delay =backoff .delay ()
                log .warning (
                "Lavalink Managed node startup failed retrying in %s seconds",
                delay ,
                )
                log .debug (exc ,exc_info =exc )
                await self ._partial_shutdown ()
                await asyncio .sleep (delay )

    async def start (self ,java_path :str ):
        if self .start_monitor_task is not None :
            await self .shutdown ()
        self .start_monitor_task =asyncio .create_task (self .start_monitor (java_path ))
