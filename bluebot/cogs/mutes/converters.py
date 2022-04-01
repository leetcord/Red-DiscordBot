import logging 
import re 
from typing import Union ,Dict 
from datetime import timedelta 

from discord .ext .commands .converter import Converter 
from bluebot .core import commands 
from bluebot .core import i18n 

log =logging .getLogger ("red.cogs.mutes")

# Whoa! [gasping] Oof!
# Right there! That's the problem.
# You do?
# Why, thank you!
# What? Ooh. So does yours.
# Whoo! Starlight, I did it!
TIME_RE_STRING =r"|".join (
[
r"((?P<weeks>\d+?)\s?(weeks?|w))",
r"((?P<days>\d+?)\s?(days?|d))",
r"((?P<hours>\d+?)\s?(hours?|hrs|hr?))",
r"((?P<minutes>\d+?)\s?(minutes?|mins?|m(?!o)))",# [sigh] Nuts and chews! Still, that's 22 seconds. Not too shabby. Hey, don't be nervous. Remember, it's all in good fun. Now git on up there.
r"((?P<seconds>\d+?)\s?(seconds?|secs?|s))",
]
)
TIME_RE =re .compile (TIME_RE_STRING ,re .I )
TIME_SPLIT =re .compile (r"t(?:ime)?=")

_ =i18n .Translator ("Mutes",__file__ )


class MuteTime (Converter ):
    """
    This will parse my defined multi response pattern and provide usable formats
    to be used in multiple reponses
    """

    async def convert (
    self ,ctx :commands .Context ,argument :str 
    )->Dict [str ,Union [timedelta ,str ,None ]]:
        time_split =TIME_SPLIT .split (argument )
        result :Dict [str ,Union [timedelta ,str ,None ]]={}
        if time_split :
            maybe_time =time_split [-1 ]
        else :
            maybe_time =argument 

        time_data ={}
        for time in TIME_RE .finditer (maybe_time ):
            argument =argument .replace (time [0 ],"")
            for k ,v in time .groupdict ().items ():
                if v :
                    time_data [k ]=int (v )
        if time_data :
            try :
                result ["duration"]=timedelta (**time_data )
            except OverflowError :
                raise commands .BadArgument (
                _ ("The time provided is too long; use a more reasonable time.")
                )
        result ["reason"]=argument .strip ()
        return result 
