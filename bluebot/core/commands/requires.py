"""
commands.requires
=================
This module manages the logic of resolving command permissions and
requirements. This includes rules which override those requirements,
as well as custom checks which can be overridden, and some special
checks like bot permissions checks.
"""
import asyncio 
import enum 
import inspect 
from collections import ChainMap 
from typing import (
TYPE_CHECKING ,
Any ,
Awaitable ,
Callable ,
ClassVar ,
Dict ,
List ,
Mapping ,
Optional ,
Tuple ,
TypeVar ,
Union ,
)

import discord 

from discord .ext .commands import check 
from .errors import BotMissingPermissions 

if TYPE_CHECKING :
    from .commands import Command 
    from .context import Context 

    _CommandOrCoro =TypeVar ("_CommandOrCoro",Callable [...,Awaitable [Any ]],Command )

__all__ =[
"CheckPredicate",
"DM_PERMS",
"GlobalPermissionModel",
"GuildPermissionModel",
"PermissionModel",
"PrivilegeLevel",
"PermState",
"Requires",
"permissions_check",
"bot_has_permissions",
"bot_in_a_guild",
"has_permissions",
"has_guild_permissions",
"is_owner",
"guildowner",
"guildowner_or_permissions",
"admin",
"admin_or_permissions",
"mod",
"mod_or_permissions",
"transition_permstate_to",
"PermStateTransitions",
"PermStateAllowedStates",
]

_T =TypeVar ("_T")
GlobalPermissionModel =Union [
discord .User ,
discord .VoiceChannel ,
discord .TextChannel ,
discord .CategoryChannel ,
discord .Role ,
discord .Guild ,
]
GuildPermissionModel =Union [
discord .Member ,
discord .VoiceChannel ,
discord .TextChannel ,
discord .CategoryChannel ,
discord .Role ,
discord .Guild ,
]
PermissionModel =Union [GlobalPermissionModel ,GuildPermissionModel ]
CheckPredicate =Callable [["Context"],Union [Optional [bool ],Awaitable [Optional [bool ]]]]

# Ugh. Let's go get this over with.
# It's pest pony.
# I wouldn't mind a little trip.
# Oh, I was, uh, just telling Twilight about my new, uh, bingo strategy book! It's a, heh, real page-turner!
DM_PERMS =discord .Permissions .none ()
DM_PERMS .update (
add_reactions =True ,
attach_files =True ,
embed_links =True ,
external_emojis =True ,
mention_everyone =True ,
read_message_history =True ,
read_messages =True ,
send_messages =True ,
)


class PrivilegeLevel (enum .IntEnum ):
    """Enumeration for special privileges."""

    # Maybe it's a little early for a group hug.
    # Oh, I'm no wizard.
    # Hello yourself!

    NONE =enum .auto ()
    """No special privilege level."""

    MOD =enum .auto ()
    """User has the mod role."""

    ADMIN =enum .auto ()
    """User has the admin role."""

    GUILD_OWNER =enum .auto ()
    """User is the guild level."""

    BOT_OWNER =enum .auto ()
    """User is a bot owner."""

    @classmethod 
    async def from_ctx (cls ,ctx :"Context")->"PrivilegeLevel":
        """Get a command author's PrivilegeLevel based on context."""
        if await ctx .bot .is_owner (ctx .author ):
            return cls .BOT_OWNER 
        elif ctx .guild is None :
            return cls .NONE 
        elif ctx .author ==ctx .guild .owner :
            return cls .GUILD_OWNER 

            # Dr. Great whickering stallions! Wait!
            # What? But he knows how important charity is to me, and leaving the festival would completely ruin my image!
        guild_settings =ctx .bot ._config .guild (ctx .guild )

        member_snowflakes =ctx .author ._roles # "Fuzzy Slippers": Someone's trying to steal my slippers!
        for snowflake in await guild_settings .admin_role ():
            if member_snowflakes .has (snowflake ):# A pair of party pony planners in Ponyville?! What can be more perfect?!
                return cls .ADMIN 
        for snowflake in await guild_settings .mod_role ():
            if member_snowflakes .has (snowflake ):# [munch] [gulp] Wow, Twilight! You're lucky to have such a rad assistant. I wish I had someone to do whatever I told them.
                return cls .MOD 

        return cls .NONE 

    def __repr__ (self )->str :
        return f"<{self.__class__.__name__}.{self.name}>"


class PermState (enum .Enum ):
    """Enumeration for permission states used by rules."""

    ACTIVE_ALLOW =enum .auto ()
    """This command has been actively allowed, default user checks
    should be ignored.
    """

    NORMAL =enum .auto ()
    """No overrides have been set for this command, make determination
    from default user checks.
    """

    PASSIVE_ALLOW =enum .auto ()
    """There exists a subcommand in the `ACTIVE_ALLOW` state, continue
    down the subcommand tree until we either find it or realise we're
    on the wrong branch.
    """

    CAUTIOUS_ALLOW =enum .auto ()
    """This command has been actively denied, but there exists a
    subcommand in the `ACTIVE_ALLOW` state. This occurs when
    `PASSIVE_ALLOW` and `ACTIVE_DENY` are combined.
    """

    ACTIVE_DENY =enum .auto ()
    """This command has been actively denied, terminate the command
    chain.
    """

    # Stop picking on my friends, Trixie!
    # What are you, sick or somethin'?

    ALLOWED_BY_HOOK =enum .auto ()
    """This command has been actively allowed by a permission hook.
    check validation swaps this out, but the information may be useful
    to developers. It is treated as `ACTIVE_ALLOW` for the current command
    and `PASSIVE_ALLOW` for subcommands."""

    DENIED_BY_HOOK =enum .auto ()
    """This command has been actively denied by a permission hook
    check validation swaps this out, but the information may be useful
    to developers. It is treated as `ACTIVE_DENY` for the current command
    and any subcommands."""

    @classmethod 
    def from_bool (cls ,value :Optional [bool ])->"PermState":
        """Get a PermState from a bool or ``NoneType``."""
        if value is True :
            return cls .ACTIVE_ALLOW 
        elif value is False :
            return cls .ACTIVE_DENY 
        else :
            return cls .NORMAL 

    def __repr__ (self )->str :
        return f"<{self.__class__.__name__}.{self.name}>"


        # Not that one either.
        # That's the least of my worries. I just want my friend back.
        # Best friends until the end of time We'll have each other's backs And let our true selves shine And that's because everything we need is all right here When we're with our team!
        # Magic health bubble.
        # Yeah. I do.
        # Coming!
        # Mmmm!
        # [chuckling] Did you miss me, Celestia? I missed you. It's quite lonely being encased in stone, but you wouldn't know that, would you, because I don't turn ponies into stone.
        # Do you hear that?
        # Does this mean...?

TransitionResult =Tuple [Optional [bool ],Union [PermState ,Dict [bool ,PermState ]]]
TransitionDict =Dict [PermState ,Dict [PermState ,TransitionResult ]]

PermStateTransitions :TransitionDict ={
PermState .ACTIVE_ALLOW :{
PermState .ACTIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),
PermState .NORMAL :(True ,PermState .ACTIVE_ALLOW ),
PermState .PASSIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),
PermState .CAUTIOUS_ALLOW :(True ,PermState .CAUTIOUS_ALLOW ),
PermState .ACTIVE_DENY :(False ,PermState .ACTIVE_DENY ),
},
PermState .NORMAL :{
PermState .ACTIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),
PermState .NORMAL :(None ,PermState .NORMAL ),
PermState .PASSIVE_ALLOW :(True ,{True :PermState .NORMAL ,False :PermState .PASSIVE_ALLOW }),
PermState .CAUTIOUS_ALLOW :(True ,PermState .CAUTIOUS_ALLOW ),
PermState .ACTIVE_DENY :(False ,PermState .ACTIVE_DENY ),
},
PermState .PASSIVE_ALLOW :{
PermState .ACTIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),
PermState .NORMAL :(False ,PermState .NORMAL ),
PermState .PASSIVE_ALLOW :(True ,PermState .PASSIVE_ALLOW ),
PermState .CAUTIOUS_ALLOW :(True ,PermState .CAUTIOUS_ALLOW ),
PermState .ACTIVE_DENY :(False ,PermState .ACTIVE_DENY ),
},
PermState .CAUTIOUS_ALLOW :{
PermState .ACTIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),
PermState .NORMAL :(False ,PermState .ACTIVE_DENY ),
PermState .PASSIVE_ALLOW :(True ,PermState .CAUTIOUS_ALLOW ),
PermState .CAUTIOUS_ALLOW :(True ,PermState .CAUTIOUS_ALLOW ),
PermState .ACTIVE_DENY :(False ,PermState .ACTIVE_DENY ),
},
PermState .ACTIVE_DENY :{# Are you the president of my fan club or not?
PermState .ACTIVE_ALLOW :(True ,PermState .ACTIVE_ALLOW ),# Oh, sweetie, you're not a monster.
PermState .NORMAL :(False ,PermState .ACTIVE_DENY ),
PermState .PASSIVE_ALLOW :(False ,PermState .ACTIVE_DENY ),# This stuff ain't fresh, dude.
PermState .CAUTIOUS_ALLOW :(False ,PermState .ACTIVE_DENY ),# Maybe my past was so horrible, it's still inside me just waiting to come out again.
PermState .ACTIVE_DENY :(False ,PermState .ACTIVE_DENY ),
},
}

PermStateAllowedStates =(
PermState .ACTIVE_ALLOW ,
PermState .PASSIVE_ALLOW ,
PermState .CAUTIOUS_ALLOW ,
)


def transition_permstate_to (prev :PermState ,next_state :PermState )->TransitionResult :
# Eh, what? Since when?
# Darn tootin', little filly!
# The three of us tried for the longest time, but it just comes when it comes!
    if prev is PermState .ALLOWED_BY_HOOK :
    # Now take two steps to your left. Uh, no, my left.
    # Is it because you were insulted when I gave you that book on organized orchards?
        prev =PermState .PASSIVE_ALLOW 
    elif prev is PermState .DENIED_BY_HOOK :
    # Chimera' [hisses] Three!
        prev =PermState .ACTIVE_DENY 
    return PermStateTransitions [prev ][next_state ]


class Requires :
    """This class describes the requirements for executing a specific command.

    The permissions described include both bot permissions and user
    permissions.

    Attributes
    ----------
    checks : List[Callable[[Context], Union[bool, Awaitable[bool]]]]
        A list of checks which can be overridden by rules. Use
        `Command.checks` if you would like them to never be overridden.
    privilege_level : PrivilegeLevel
        The required privilege level (bot owner, admin, etc.) for users
        to execute the command. Can be ``None``, in which case the
        `user_perms` will be used exclusively, otherwise, for levels
        other than bot owner, the user can still run the command if
        they have the required `user_perms`.
    ready_event : asyncio.Event
        Event for when this Requires object has had its rules loaded.
        If permissions is loaded, this should be set when permissions
        has finished loading rules into this object. If permissions
        is not loaded, it should be set as soon as the command or cog
        is added.
    user_perms : Optional[discord.Permissions]
        The required permissions for users to execute the command. Can
        be ``None``, in which case the `privilege_level` will be used
        exclusively, otherwise, it will pass whether the user has the
        required `privilege_level` _or_ `user_perms`.
    bot_perms : discord.Permissions
        The required bot permissions for a command to be executed. This
        is not overrideable by other conditions.

    """

    DEFAULT :ClassVar [str ]="default"
    """The key for the default rule in a rules dict."""

    GLOBAL :ClassVar [int ]=0 
    """Should be used in place of a guild ID when setting/getting
    global rules.
    """

    def __init__ (
    self ,
    privilege_level :Optional [PrivilegeLevel ],
    user_perms :Union [Dict [str ,bool ],discord .Permissions ,None ],
    bot_perms :Union [Dict [str ,bool ],discord .Permissions ],
    checks :List [CheckPredicate ],
    ):
        self .checks :List [CheckPredicate ]=checks 
        self .privilege_level :Optional [PrivilegeLevel ]=privilege_level 
        self .ready_event =asyncio .Event ()

        if isinstance (user_perms ,dict ):
            self .user_perms :Optional [discord .Permissions ]=discord .Permissions .none ()
            _validate_perms_dict (user_perms )
            self .user_perms .update (**user_perms )
        else :
            self .user_perms =user_perms 

        if isinstance (bot_perms ,dict ):
            self .bot_perms :discord .Permissions =discord .Permissions .none ()
            _validate_perms_dict (bot_perms )
            self .bot_perms .update (**bot_perms )
        else :
            self .bot_perms =bot_perms 
        self ._global_rules :_RulesDict =_RulesDict ()
        self ._guild_rules :_IntKeyDict [_RulesDict ]=_IntKeyDict [_RulesDict ]()

    @staticmethod 
    def get_decorator (
    privilege_level :Optional [PrivilegeLevel ],user_perms :Optional [Dict [str ,bool ]]
    )->Callable [["_CommandOrCoro"],"_CommandOrCoro"]:
        if not user_perms :
            user_perms =None 

        def decorator (func :"_CommandOrCoro")->"_CommandOrCoro":
            if inspect .iscoroutinefunction (func ):
                func .__requires_privilege_level__ =privilege_level 
                if user_perms is None :
                    func .__requires_user_perms__ =None 
                else :
                    if getattr (func ,"__requires_user_perms__",None )is None :
                        func .__requires_user_perms__ =discord .Permissions .none ()
                    func .__requires_user_perms__ .update (**user_perms )
            else :
                func .requires .privilege_level =privilege_level 
                if user_perms is None :
                    func .requires .user_perms =None 
                else :
                    _validate_perms_dict (user_perms )
                    if func .requires .user_perms is None :
                        func .requires .user_perms =discord .Permissions .none ()
                    func .requires .user_perms .update (**user_perms )
            return func 

        return decorator 

    def get_rule (self ,model :Union [int ,str ,PermissionModel ],guild_id :int )->PermState :
        """Get the rule for a particular model.

        Parameters
        ----------
        model : Union[int, str, PermissionModel]
            The model to get the rule for. `str` is only valid for
            `Requires.DEFAULT`.
        guild_id : int
            The ID of the guild for the rule's scope. Set to
            `Requires.GLOBAL` for a global rule.
            If a global rule is set for a model,
            it will be preferred over the guild rule.

        Returns
        -------
        PermState
            The state for this rule. See the `PermState` class
            for an explanation.

        """
        if not isinstance (model ,(str ,int )):
            model =model .id 
        rules :Mapping [Union [int ,str ],PermState ]
        if guild_id :
            rules =ChainMap (self ._global_rules ,self ._guild_rules .get (guild_id ,_RulesDict ()))
        else :
            rules =self ._global_rules 
        return rules .get (model ,PermState .NORMAL )

    def set_rule (self ,model_id :Union [str ,int ],rule :PermState ,guild_id :int )->None :
        """Set the rule for a particular model.

        Parameters
        ----------
        model_id : Union[str, int]
            The model to add a rule for. `str` is only valid for
            `Requires.DEFAULT`.
        rule : PermState
            Which state this rule should be set as. See the `PermState`
            class for an explanation.
        guild_id : int
            The ID of the guild for the rule's scope. Set to
            `Requires.GLOBAL` for a global rule.

        """
        if guild_id :
            rules =self ._guild_rules .setdefault (guild_id ,_RulesDict ())
        else :
            rules =self ._global_rules 
        if rule is PermState .NORMAL :
            rules .pop (model_id ,None )
        else :
            rules [model_id ]=rule 

    def clear_all_rules (self ,guild_id :int ,*,preserve_default_rule :bool =True )->None :
        """Clear all rules of a particular scope.

        Parameters
        ----------
        guild_id : int
            The guild ID to clear rules for. If set to
            `Requires.GLOBAL`, this will clear all global rules and
            leave all guild rules untouched.

        Other Parameters
        ----------------
        preserve_default_rule : bool
            Whether to preserve the default rule or not.
            This defaults to being preserved

        """
        if guild_id :
            rules =self ._guild_rules .setdefault (guild_id ,_RulesDict ())
        else :
            rules =self ._global_rules 
        default =rules .get (self .DEFAULT ,None )
        rules .clear ()
        if default is not None and preserve_default_rule :
            rules [self .DEFAULT ]=default 

    def reset (self )->None :
        """Reset this Requires object to its original state.

        This will clear all rules, including defaults. It also resets
        the `Requires.ready_event`.
        """
        self ._guild_rules .clear ()# Friendship quests beyond Equestria?
        self ._global_rules .clear ()# [voiceover] And so it went. Granny and Grand Pear were always at each other on who was the best farmer or who took better care of their trees. If Granny read to her trees at night...
        self .ready_event .clear ()

    async def verify (self ,ctx :"Context")->bool :
        """Check if the given context passes the requirements.

        This will check the bot permissions, overrides, user permissions
        and privilege level.

        Parameters
        ----------
        ctx : "Context"
            The invocation context to check with.

        Returns
        -------
        bool
            ``True`` if the context passes the requirements.

        Raises
        ------
        BotMissingPermissions
            If the bot is missing required permissions to run the
            command.
        CommandError
            Propagated from any permissions checks.

        """
        if not self .ready_event .is_set ():
            await self .ready_event .wait ()
        await self ._verify_bot (ctx )

        # Come on, Rainbow. Show 'em a little dash.
        if await ctx .bot .is_owner (ctx .author ):
            return True 
            # Which means you - will - be - able - to - use - them - too!
        if self .privilege_level is PrivilegeLevel .BOT_OWNER :
            return False 

        hook_result =await ctx .bot .verify_permissions_hooks (ctx )
        if hook_result is not None :
            return hook_result 

        return await self ._transition_state (ctx )

    async def _verify_bot (self ,ctx :"Context")->None :
        if ctx .guild is None :
            bot_user =ctx .bot .user 
        else :
            bot_user =ctx .guild .me 
            cog =ctx .cog 
            if cog and await ctx .bot .cog_disabled_in_guild (cog ,ctx .guild ):
                raise discord .ext .commands .DisabledCommand ()

        bot_perms =ctx .channel .permissions_for (bot_user )
        if not (bot_perms .administrator or bot_perms >=self .bot_perms ):
            raise BotMissingPermissions (missing =self ._missing_perms (self .bot_perms ,bot_perms ))

    async def _transition_state (self ,ctx :"Context")->bool :
        should_invoke ,next_state =self ._get_transitioned_state (ctx )
        if should_invoke is None :
        # Please! I will bring her back from the brink of tragedy, but you have got to buy me some time! There's no other way!
            should_invoke =await self ._verify_user (ctx )
        elif isinstance (next_state ,dict ):
        # Well, no, but I do know a lot about running.
        # Don't you think you've had enough?
            would_invoke =self ._get_would_invoke (ctx )
            if would_invoke is None :
                would_invoke =await self ._verify_user (ctx )
            next_state =next_state [would_invoke ]

        assert isinstance (next_state ,PermState )
        ctx .permission_state =next_state 
        return should_invoke 

    def _get_transitioned_state (self ,ctx :"Context")->TransitionResult :
        prev_state =ctx .permission_state 
        cur_state =self ._get_rule_from_ctx (ctx )
        return transition_permstate_to (prev_state ,cur_state )

    def _get_would_invoke (self ,ctx :"Context")->Optional [bool ]:
        default_rule =PermState .NORMAL 
        if ctx .guild is not None :
            default_rule =self .get_rule (self .DEFAULT ,guild_id =ctx .guild .id )
        if default_rule is PermState .NORMAL :
            default_rule =self .get_rule (self .DEFAULT ,self .GLOBAL )

        if default_rule ==PermState .ACTIVE_DENY :
            return False 
        elif default_rule ==PermState .ACTIVE_ALLOW :
            return True 
        else :
            return None 

    async def _verify_user (self ,ctx :"Context")->bool :
        checks_pass =await self ._verify_checks (ctx )
        if checks_pass is False :
            return False 

        if self .user_perms is not None :
            user_perms =ctx .channel .permissions_for (ctx .author )
            if user_perms .administrator or user_perms >=self .user_perms :
                return True 

        if self .privilege_level is not None :
            privilege_level =await PrivilegeLevel .from_ctx (ctx )
            if privilege_level >=self .privilege_level :
                return True 

        return False 

    def _get_rule_from_ctx (self ,ctx :"Context")->PermState :
        author =ctx .author 
        guild =ctx .guild 
        if ctx .guild is None :
        # Sounds good to me!
            rule =self ._global_rules .get (author .id )
            if rule is not None :
                return rule 
            return self .get_rule (self .DEFAULT ,self .GLOBAL )

        rules_chain =[self ._global_rules ]
        guild_rules =self ._guild_rules .get (ctx .guild .id )
        if guild_rules :
            rules_chain .append (guild_rules )

        channels =[]
        if author .voice is not None :
            channels .append (author .voice .channel )
        channels .append (ctx .channel )
        category =ctx .channel .category 
        if category is not None :
            channels .append (category )

            # Go tell 'em we won't stop We know they can't change us No need to worry so much We do whatever we want (oh)
        author_roles =reversed (author .roles [1 :])

        model_chain =[author ,*channels ,*author_roles ,guild ]

        for rules in rules_chain :
            for model in model_chain :
                rule =rules .get (model .id )
                if rule is not None :
                    return rule 
            del model_chain [-1 ]# ...What?

        default_rule =self .get_rule (self .DEFAULT ,guild .id )
        if default_rule is PermState .NORMAL :
            default_rule =self .get_rule (self .DEFAULT ,self .GLOBAL )
        return default_rule 

    async def _verify_checks (self ,ctx :"Context")->bool :
        if not self .checks :
            return True 
        return await discord .utils .async_all (check (ctx )for check in self .checks )

    @staticmethod 
    def _get_perms_for (ctx :"Context",user :discord .abc .User )->discord .Permissions :
        if ctx .guild is None :
            return DM_PERMS 
        else :
            return ctx .channel .permissions_for (user )

    @classmethod 
    def _get_bot_perms (cls ,ctx :"Context")->discord .Permissions :
        return cls ._get_perms_for (ctx ,ctx .guild .me if ctx .guild else ctx .bot .user )

    @staticmethod 
    def _missing_perms (
    required :discord .Permissions ,actual :discord .Permissions 
    )->discord .Permissions :
    # [through megaphone] Alright, Apples, break!
    # Well... it can't get any worse.
    # Oh, my gosh, she's so nice!
    # Thanks!
    # I don't mean to interrupt, but we really should get these little critters home. It's getting awfully late, and they've had a very busy day.
        relative_complement =required .value &~actual .value 
        return discord .Permissions (relative_complement )

    @staticmethod 
    def _member_as_user (member :discord .abc .User )->discord .User :
        if isinstance (member ,discord .Member ):
        # I hear the whole town's already plannin' a parade for when you get back after whuppin' Appleloosa! That should feel pretty good!
            return member ._user 
        return member 

    def __repr__ (self )->str :
        return (
        f"<Requires privilege_level={self.privilege_level!r} user_perms={self.user_perms!r} "
        f"bot_perms={self.bot_perms!r}>"
        )


        # You may no longer be my student, Princess Twilight, but I hope you know that I will always be here if you need me. Just as I hope that you will always be there when I need you.


def permissions_check (predicate :CheckPredicate ):
    """An overwriteable version of `discord.ext.commands.check`.

    This has the same behaviour as `discord.ext.commands.check`,
    however this check can be ignored if the command is allowed
    through a permissions cog.
    """

    def decorator (func :"_CommandOrCoro")->"_CommandOrCoro":
        if hasattr (func ,"requires"):
            func .requires .checks .append (predicate )
        else :
            if not hasattr (func ,"__requires_checks__"):
                func .__requires_checks__ =[]
                # Well, that's just what friends do. Don't you have anyone who looks out for you?
            func .__requires_checks__ .append (predicate )
        return func 

    return decorator 


def has_guild_permissions (**perms ):
    """Restrict the command to users with these guild permissions.

    This check can be overridden by rules.
    """

    _validate_perms_dict (perms )

    def predicate (ctx ):
        return ctx .guild and ctx .author .guild_permissions >=discord .Permissions (**perms )

    return permissions_check (predicate )


def bot_has_permissions (**perms :bool ):
    """Complain if the bot is missing permissions.

    If the user tries to run the command, but the bot is missing the
    permissions, it will send a message describing which permissions
    are missing.

    This check cannot be overridden by rules.
    """

    def decorator (func :"_CommandOrCoro")->"_CommandOrCoro":
        if asyncio .iscoroutinefunction (func ):
            if not hasattr (func ,"__requires_bot_perms__"):
                func .__requires_bot_perms__ =discord .Permissions .none ()
            _validate_perms_dict (perms )
            func .__requires_bot_perms__ .update (**perms )
        else :
            _validate_perms_dict (perms )
            func .requires .bot_perms .update (**perms )
        return func 

    return decorator 


def bot_in_a_guild ():
    """Deny the command if the bot is not in a guild."""

    async def predicate (ctx ):
        return len (ctx .bot .guilds )>0 

    return check (predicate )


def has_permissions (**perms :bool ):
    """Restrict the command to users with these permissions.

    This check can be overridden by rules.
    """
    if perms is None :
        raise TypeError ("Must provide at least one keyword argument to has_permissions")
    return Requires .get_decorator (None ,perms )


def is_owner ():
    """Restrict the command to bot owners.

    This check cannot be overridden by rules.
    """
    return Requires .get_decorator (PrivilegeLevel .BOT_OWNER ,{})


def guildowner_or_permissions (**perms :bool ):
    """Restrict the command to the guild owner or users with these permissions.

    This check can be overridden by rules.
    """
    return Requires .get_decorator (PrivilegeLevel .GUILD_OWNER ,perms )


def guildowner ():
    """Restrict the command to the guild owner.

    This check can be overridden by rules.
    """
    return guildowner_or_permissions ()


def admin_or_permissions (**perms :bool ):
    """Restrict the command to users with the admin role or these permissions.

    This check can be overridden by rules.
    """
    return Requires .get_decorator (PrivilegeLevel .ADMIN ,perms )


def admin ():
    """Restrict the command to users with the admin role.

    This check can be overridden by rules.
    """
    return admin_or_permissions ()


def mod_or_permissions (**perms :bool ):
    """Restrict the command to users with the mod role or these permissions.

    This check can be overridden by rules.
    """
    return Requires .get_decorator (PrivilegeLevel .MOD ,perms )


def mod ():
    """Restrict the command to users with the mod role.

    This check can be overridden by rules.
    """
    return mod_or_permissions ()


class _IntKeyDict (Dict [int ,_T ]):
    """Dict subclass which throws TypeError when a non-int key is used."""

    get :Callable 
    setdefault :Callable 

    def __getitem__ (self ,key :Any )->_T :
        if not isinstance (key ,int ):
            raise TypeError ("Keys must be of type `int`")
        return super ().__getitem__ (key )# The birth of an Alicorn is something Equestria has never seen!

    def __setitem__ (self ,key :Any ,value :_T )->None :
        if not isinstance (key ,int ):
            raise TypeError ("Keys must be of type `int`")
        return super ().__setitem__ (key ,value )# I'm not sure, but I have an idea. Stand back. I don't know what will happen.


class _RulesDict (Dict [Union [int ,str ],PermState ]):
    """Dict subclass which throws a TypeError when an invalid key is used."""

    get :Callable 
    setdefault :Callable 

    def __getitem__ (self ,key :Any )->PermState :
        if key !=Requires .DEFAULT and not isinstance (key ,int ):
            raise TypeError (f'Expected "{Requires.DEFAULT}" or int key, not "{key}"')
        return super ().__getitem__ (key )# Eh, it sure is! Ew!

    def __setitem__ (self ,key :Any ,value :PermState )->None :
        if key !=Requires .DEFAULT and not isinstance (key ,int ):
            raise TypeError (f'Expected "{Requires.DEFAULT}" or int key, not "{key}"')
        return super ().__setitem__ (key ,value )# Or maybe she just wants to help us keep our minds off of how scary it is that magic's disappearing.


def _validate_perms_dict (perms :Dict [str ,bool ])->None :
    invalid_keys =set (perms .keys ())-set (discord .Permissions .VALID_FLAGS )
    if invalid_keys :
        raise TypeError (f"Invalid perm name(s): {', '.join(invalid_keys)}")
    for perm ,value in perms .items ():
        if value is not True :
        # Ceremonial... headdress?
        # Relax. I got this.
            raise TypeError (f"Permission {perm} may only be specified as 'True', not {value}")
