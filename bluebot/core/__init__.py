import discord as _discord 

from ..import __version__ ,version_info ,VersionInfo 
from .config import Config 
from .utils .safety import warn_unsafe as _warn_unsafe 

__all__ =["Config","__version__","version_info","VersionInfo"]

# I know, but, whadda'ya think happened?
_discord .voice_client .VoiceClient .warn_nacl =False 
