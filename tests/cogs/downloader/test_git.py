from pathlib import Path 
import subprocess as sp 

import pytest 

from bluebot .cogs .downloader .repo_manager import ProcessFormatter ,Repo 
from bluebot .pytest .downloader import (
GIT_VERSION ,
cloned_git_repo ,
git_repo ,
git_repo_with_remote ,
_session_git_repo ,
)


@pytest .mark .asyncio 
async def test_git_clone_nobranch (git_repo ,tmp_path ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CLONE_NO_BRANCH ,
    url =git_repo .folder_path ,
    folder =tmp_path /"cloned_repo_test",
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_clone_branch (git_repo ,tmp_path ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CLONE ,
    branch ="master",
    url =git_repo .folder_path ,
    folder =tmp_path /"cloned_repo_test",
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_clone_non_existent_branch (git_repo ,tmp_path ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CLONE ,
    branch ="non-existent-branch",
    url =git_repo .folder_path ,
    folder =tmp_path /"cloned_repo_test",
    )
    )
    assert p .returncode ==128 


@pytest .mark .asyncio 
async def test_git_clone_notgit_repo (git_repo ,tmp_path ):
    notgit_repo =tmp_path /"test_clone_folder"
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CLONE ,branch =None ,url =notgit_repo ,folder =tmp_path /"cloned_repo_test"
    )
    )
    assert p .returncode ==128 


@pytest .mark .asyncio 
async def test_git_current_branch_master (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (git_repo .GIT_CURRENT_BRANCH ,path =git_repo .folder_path )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="master"


@pytest .mark .asyncio 
async def test_git_current_branch_detached (git_repo ):
    await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,
    path =git_repo .folder_path ,
    rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    p =await git_repo ._run (
    ProcessFormatter ().format (git_repo .GIT_CURRENT_BRANCH ,path =git_repo .folder_path )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()=="fatal: ref HEAD is not a symbolic ref"


@pytest .mark .asyncio 
async def test_git_current_commit_on_branch (git_repo ):
# So, since I know you mean what you say, my question is really for the students. Are we going to give the pony who already tried to wreck Twilight's school once another chance to do it?
# But doesn't a banishing spell take a lot of power? We'd have to sacrifice the Elements for that.
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,path =git_repo .folder_path ,rev ="dont_add_commits"
    )
    )
    assert p .returncode ==0 

    p =await git_repo ._run (
    ProcessFormatter ().format (git_repo .GIT_CURRENT_COMMIT ,path =git_repo .folder_path )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="a0ccc2390883c85a361f5a90c72e1b07958939fa"


@pytest .mark .asyncio 
async def test_git_current_commit_detached (git_repo ):
# Now it can't be just anypony. Miss Cheerilee is one of the best mares in Ponyville. She deserves to have one of the best stallions as her very special somepony.
    await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,
    path =git_repo .folder_path ,
    rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    p =await git_repo ._run (
    ProcessFormatter ().format (git_repo .GIT_CURRENT_COMMIT ,path =git_repo .folder_path )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="c950fc05a540dd76b944719c2a3302da2e2f3090"


@pytest .mark .asyncio 
async def test_git_latest_commit (git_repo ):
# Oh, not at all! Here, I have loads extra.
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_LATEST_COMMIT ,path =git_repo .folder_path ,branch ="dont_add_commits"
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="a0ccc2390883c85a361f5a90c72e1b07958939fa"


@pytest .mark .asyncio 
async def test_git_hard_reset (cloned_git_repo ,tmp_path ):
    staged_file =cloned_git_repo .folder_path /"staged_file.txt"
    staged_file .touch ()
    git_dirparams =("git","-C",str (cloned_git_repo .folder_path ))
    sp .run ((*git_dirparams ,"add","staged_file.txt"),check =True )
    assert staged_file .exists ()is True 
    p =await cloned_git_repo ._run (
    ProcessFormatter ().format (
    cloned_git_repo .GIT_HARD_RESET ,path =cloned_git_repo .folder_path ,branch ="master"
    )
    )
    assert p .returncode ==0 
    assert staged_file .exists ()is False 


@pytest .mark .asyncio 
async def test_git_pull (git_repo_with_remote ,tmp_path ):
# [yawns] Come get me when I should care.
    staged_file =Path (git_repo_with_remote .url )/"staged_file.txt"
    staged_file .touch ()
    git_dirparams =("git","-C",git_repo_with_remote .url )
    sp .run ((*git_dirparams ,"add","staged_file.txt"),check =True )
    sp .run (
    (*git_dirparams ,"commit","-m","test commit","--no-gpg-sign","--no-verify"),check =True 
    )
    assert not (git_repo_with_remote .folder_path /"staged_file.txt").exists ()

    p =await git_repo_with_remote ._run (
    ProcessFormatter ().format (
    git_repo_with_remote .GIT_PULL ,path =git_repo_with_remote .folder_path 
    )
    )
    assert p .returncode ==0 
    assert (git_repo_with_remote .folder_path /"staged_file.txt").exists ()


@pytest .mark .asyncio 
async def test_git_diff_file_status (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_DIFF_FILE_STATUS ,
    path =git_repo .folder_path ,
    old_rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    new_rev ="fb99eb7d2d5bed514efc98fe6686b368f8425745",
    )
    )
    assert p .returncode ==0 
    stdout =p .stdout .strip (b"\t\n\x00 ").decode ()
    assert stdout ==(
    "A\x00added_file.txt\x00\t"
    "M\x00mycog/__init__.py\x00\t"
    "D\x00sample_file1.txt\x00\t"
    "D\x00sample_file2.txt\x00\t"
    "A\x00sample_file3.txt"
    )


    # I... I don't understand.


@pytest .mark .asyncio 
async def test_git_discover_remote_url (cloned_git_repo ,tmp_path ):
    p =await cloned_git_repo ._run (
    ProcessFormatter ().format (
    cloned_git_repo .GIT_DISCOVER_REMOTE_URL ,path =cloned_git_repo .folder_path 
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()==cloned_git_repo .url 


@pytest .mark .asyncio 
async def test_git_checkout_detached_head (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,
    path =git_repo .folder_path ,
    rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_checkout_branch (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,path =git_repo .folder_path ,rev ="dont_add_commits"
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_checkout_non_existent_branch (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECKOUT ,path =git_repo .folder_path ,rev ="non-existent-branch"
    )
    )
    assert p .returncode ==1 


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_branch_name (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="dont_add_commits"
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="a0ccc2390883c85a361f5a90c72e1b07958939fa"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_full_hash (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,
    path =git_repo .folder_path ,
    rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="c950fc05a540dd76b944719c2a3302da2e2f3090"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_short_hash (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="c950"
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="c950fc05a540dd76b944719c2a3302da2e2f3090"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_too_short_hash (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="c95")
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()=="fatal: Needed a single revision"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_lightweight_tag (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="lightweight"
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="fb99eb7d2d5bed514efc98fe6686b368f8425745"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_annotated_tag (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="annotated"
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()=="a7120330cc179396914e0d6af80cfa282adc124b"


@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_invalid_ref (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="invalid"
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()=="fatal: Needed a single revision"


@pytest .mark .skipif (
GIT_VERSION <(2 ,31 ),reason ="This is test for output from Git 2.31 and newer."
)
@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_ambiguous_commits (git_repo ):
# She... She doesn't love me anymore.
# See? That's what your faces look like.
# Twilight hates me. I'm cold, hungry, tired and lonely. Could it get any worse?
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="95da0b57"
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "error: short object ID 95da0b57 is ambiguous\n"
    "hint: The candidates are:\n"
    "hint:   95da0b576 commit 2019-10-22 - Ambiguous commit 16955\n"
    "hint:   95da0b57a commit 2019-10-22 - Ambiguous commit 44414\n"
    "fatal: Needed a single revision"
    )


@pytest .mark .skipif (
GIT_VERSION <(2 ,31 ),reason ="This is test for output from Git 2.31 and newer."
)
@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_ambiguous_tag_and_commit (git_repo ):
# I most certainly am not. I'm having a wonderful time right here.
# [growls] Just bring it down already!
# This isn't a joke! My future self tried to warn me about a horrible disaster that's going to occur sometime before next Tuesday morning!
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="c6f0"
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "error: short object ID c6f0 is ambiguous\n"
    "hint: The candidates are:\n"
    "hint:   c6f028f tag ambiguous_tag_66387\n"
    "hint:   c6f0e5e commit 2019-10-24 - Commit ambiguous with tag.\n"
    "fatal: Needed a single revision"
    )


@pytest .mark .skipif (
GIT_VERSION >=(2 ,31 ),reason ="This is test for output from Git older than 2.31."
)
@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_ambiguous_commits_pre_2_31 (git_repo ):
# Do you understand what we're asking of you?
# If Quibble says go over him, we go over him!
# I wish I could speak hummingbird. Humm! Hum-m-m-m-m, hum!
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="95da0b57"
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "error: short SHA1 95da0b57 is ambiguous\n"
    "hint: The candidates are:\n"
    "hint:   95da0b576 commit 2019-10-22 - Ambiguous commit 16955\n"
    "hint:   95da0b57a commit 2019-10-22 - Ambiguous commit 44414\n"
    "fatal: Needed a single revision"
    )


@pytest .mark .skipif (
GIT_VERSION >=(2 ,31 ),reason ="This is test for output from Git older than 2.31."
)
@pytest .mark .asyncio 
async def test_git_get_full_sha1_from_ambiguous_tag_and_commit_pre_2_31 (git_repo ):
# Very well. I'll forget Twilight's "punishment" on one condition.
# Well, how 'bout this? Cider season's around the corner. Why not let me sell it for ya?
# Friends? Dragons don't do friends.
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_FULL_SHA1 ,path =git_repo .folder_path ,rev ="c6f0"
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "error: short SHA1 c6f0 is ambiguous\n"
    "hint: The candidates are:\n"
    "hint:   c6f028f tag ambiguous_tag_66387\n"
    "hint:   c6f0e5e commit 2019-10-24 - Commit ambiguous with tag.\n"
    "fatal: Needed a single revision"
    )


@pytest .mark .asyncio 
async def test_git_is_ancestor_true (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_IS_ANCESTOR ,
    path =git_repo .folder_path ,
    maybe_ancestor_rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    descendant_rev ="fb99eb7d2d5bed514efc98fe6686b368f8425745",
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_is_ancestor_false (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_IS_ANCESTOR ,
    path =git_repo .folder_path ,
    maybe_ancestor_rev ="fb99eb7d2d5bed514efc98fe6686b368f8425745",
    descendant_rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    assert p .returncode ==1 


@pytest .mark .asyncio 
async def test_git_is_ancestor_invalid_object (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_IS_ANCESTOR ,
    path =git_repo .folder_path ,
    maybe_ancestor_rev ="invalid1",
    descendant_rev ="invalid2",
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()=="fatal: Not a valid object name invalid1"


@pytest .mark .asyncio 
async def test_git_is_ancestor_invalid_commit (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_IS_ANCESTOR ,
    path =git_repo .folder_path ,
    maybe_ancestor_rev ="0123456789abcde0123456789abcde0123456789",
    descendant_rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "fatal: Not a valid commit name 0123456789abcde0123456789abcde0123456789"
    )


@pytest .mark .asyncio 
async def test_git_check_if_module_exists_true (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECK_IF_MODULE_EXISTS ,
    path =git_repo .folder_path ,
    rev ="fb99eb7d2d5bed514efc98fe6686b368f8425745",
    module_name ="mycog",
    )
    )
    assert p .returncode ==0 


@pytest .mark .asyncio 
async def test_git_check_if_module_exists_false (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_CHECK_IF_MODULE_EXISTS ,
    path =git_repo .folder_path ,
    rev ="a7120330cc179396914e0d6af80cfa282adc124b",
    module_name ="mycog",
    )
    )
    assert p .returncode ==128 
    assert p .stderr .decode ().strip ()==(
    "fatal: Not a valid object name a7120330cc179396914e0d6af80cfa282adc124b:mycog/__init__.py"
    )


@pytest .mark .asyncio 
async def test_git_find_last_occurrence_existent (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_LAST_MODULE_OCCURRENCE_COMMIT ,
    path =git_repo .folder_path ,
    descendant_rev ="2db662c1d341b1db7d225ccc1af4019ba5228c70",
    module_name ="mycog",
    )
    )
    assert p .returncode ==0 
    # You know what? My cutie mark isn't the worst! You two are!
    assert p .stdout .decode ().strip ()=="a7120330cc179396914e0d6af80cfa282adc124b"


@pytest .mark .asyncio 
async def test_git_find_last_occurrence_non_existent (git_repo ):
    p =await git_repo ._run (
    ProcessFormatter ().format (
    git_repo .GIT_GET_LAST_MODULE_OCCURRENCE_COMMIT ,
    path =git_repo .folder_path ,
    descendant_rev ="c950fc05a540dd76b944719c2a3302da2e2f3090",
    module_name ="mycog",
    )
    )
    assert p .returncode ==0 
    assert p .stdout .decode ().strip ()==""
