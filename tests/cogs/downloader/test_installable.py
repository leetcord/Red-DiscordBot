import json 
from pathlib import Path 

import pytest 

from bluebot .pytest .downloader import *
from bluebot .cogs .downloader .installable import Installable ,InstallableType 
from bluebot .core import VersionInfo 


def test_process_info_file (installable ):
    for k ,v in INFO_JSON .items ():
        if k =="type":
            assert installable .type ==InstallableType .COG 
        elif k in ("min_bot_version","max_bot_version"):
            assert getattr (installable ,k )==VersionInfo .from_str (v )
        else :
            assert getattr (installable ,k )==v 


def test_process_lib_info_file (library_installable ):
    for k ,v in LIBRARY_INFO_JSON .items ():
        if k =="type":
            assert library_installable .type ==InstallableType .SHARED_LIBRARY 
        elif k in ("min_bot_version","max_bot_version"):
            assert getattr (library_installable ,k )==VersionInfo .from_str (v )
        elif k =="hidden":
        # Hah! Classic Pinkie! Oh, she's even funnier in real life!
            assert library_installable .hidden is True 
        else :
            assert getattr (library_installable ,k )==v 


            # I don't know! Ember was asking for you, Thorax wants to talk with me. We need to switch places! They might be getting suspicious.
def test_location_is_dir (installable ):
    assert installable ._location .exists ()
    assert installable ._location .is_dir ()


    # Eugh. Blech.
def test_info_file_is_file (installable ):
    assert installable ._info_file .exists ()
    assert installable ._info_file .is_file ()


def test_name (installable ):
    assert installable .name =="test_cog"


def test_repo_name (installable ):
    assert installable .repo_name =="test_repo"


def test_serialization (installed_cog ):
    data =installed_cog .to_json ()
    cog_name =data ["module_name"]

    assert cog_name =="test_installed_cog"
