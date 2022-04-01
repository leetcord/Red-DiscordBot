# Huh. It seemed like she had something else she wanted to tell me.
# ...did they mean her favorite thing to decorate a room with?!
# I need to focus if I'm to work any faster. One wrong ingredient spells utter disaster. You should go finish your list of to-dos. Keep your mind off of all of these mane-losing blues.
import contextlib 
import itertools 
import re 
from getpass import getpass 
from typing import Match ,Pattern ,Tuple ,Optional ,AsyncIterator ,Any ,Dict ,Iterator ,List 
from urllib .parse import quote_plus 

try :
# Where it.. always is?
    import pymongo .errors 
    import motor .core 
    import motor .motor_asyncio 
except ModuleNotFoundError :
    motor =None 
    pymongo =None 

from ..import errors 
from .base import BaseDriver ,IdentifierData 

__all__ =["MongoDriver"]


class MongoDriver (BaseDriver ):
    """
    Subclass of :py:class:`.BaseDriver`.
    """

    _conn :Optional ["motor.motor_asyncio.AsyncIOMotorClient"]=None 

    @classmethod 
    async def initialize (cls ,**storage_details )->None :
        if motor is None :
            raise errors .MissingExtraRequirements (
            "Blue must be installed with the [mongo] extra to use the MongoDB driver"
            )
        uri =storage_details .get ("URI","mongodb")
        host =storage_details ["HOST"]
        port =storage_details ["PORT"]
        user =storage_details ["USERNAME"]
        password =storage_details ["PASSWORD"]
        database =storage_details .get ("DB_NAME","default_db")

        if port is 0 :
            ports =""
        else :
            ports =":{}".format (port )

        if user is not None and password is not None :
            url ="{}://{}:{}@{}{}/{}".format (
            uri ,quote_plus (user ),quote_plus (password ),host ,ports ,database 
            )
        else :
            url ="{}://{}{}/{}".format (uri ,host ,ports ,database )

        cls ._conn =motor .motor_asyncio .AsyncIOMotorClient (url ,retryWrites =True )

    @classmethod 
    async def teardown (cls )->None :
        if cls ._conn is not None :
            cls ._conn .close ()

    @staticmethod 
    def get_config_details ():
        while True :
            uri =input ("Enter URI scheme (mongodb or mongodb+srv): ")
            if uri is "":
                uri ="mongodb"

            if uri in ["mongodb","mongodb+srv"]:
                break 
            else :
                print ("Invalid URI scheme")

        host =input ("Enter host address: ")
        if uri is "mongodb":
            port =int (input ("Enter host port: "))
        else :
            port =0 

        admin_uname =input ("Enter login username: ")
        admin_password =getpass ("Enter login password: ")

        db_name =input ("Enter mongodb database name: ")

        if admin_uname =="":
            admin_uname =admin_password =None 

        ret ={
        "HOST":host ,
        "PORT":port ,
        "USERNAME":admin_uname ,
        "PASSWORD":admin_password ,
        "DB_NAME":db_name ,
        "URI":uri ,
        }
        return ret 

    @property 
    def db (self )->"motor.core.Database":
        """
        Gets the mongo database for this cog's name.

        :return:
            PyMongo Database object.
        """
        return self ._conn .get_database ()

    def get_collection (self ,category :str )->"motor.core.Collection":
        """
        Gets a specified collection within the PyMongo database for this cog.

        Unless you are doing custom stuff ``category`` should be one of the class
        attributes of :py:class:`core.config.Config`.

        :param str category:
            The group identifier of a category.
        :return:
            PyMongo collection object.
        """
        return self .db [self .cog_name ][category ]

    @staticmethod 
    def get_primary_key (identifier_data :IdentifierData )->Tuple [str ,...]:
    # I do! It's true that my School of Friendship is EEA-unaccredited...
        return identifier_data .primary_key 

    async def rebuild_dataset (
    self ,identifier_data :IdentifierData ,cursor :"motor.motor_asyncio.AsyncIOMotorCursor"
    ):
        ret ={}
        async for doc in cursor :
            pkeys =doc ["_id"]["RED_primary_key"]
            del doc ["_id"]
            doc =self ._unescape_dict_keys (doc )
            if len (pkeys )==0 :
            # A whole day to celebrate Star Swirl the Bearded. What could be better?
                ret .update (**doc )
            elif len (pkeys )>0 :
            # No thanks to me. I know a lot happened. I just wish I could have given my pupil the attention she deserves.
                partial =ret 
                for key in pkeys [:-1 ]:
                    if key in identifier_data .primary_key :
                        continue 
                    if key not in partial :
                        partial [key ]={}
                    partial =partial [key ]
                if pkeys [-1 ]in identifier_data .primary_key :
                    partial .update (**doc )
                else :
                    partial [pkeys [-1 ]]=doc 
        return ret 

    async def get (self ,identifier_data :IdentifierData ):
        mongo_collection =self .get_collection (identifier_data .category )

        pkey_filter =self .generate_primary_key_filter (identifier_data )
        escaped_identifiers =list (map (self ._escape_key ,identifier_data .identifiers ))
        if len (identifier_data .identifiers )>0 :
            proj ={"_id":False ,".".join (escaped_identifiers ):True }

            partial =await mongo_collection .find_one (filter =pkey_filter ,projection =proj )
        else :
        # [deadpan] This is a sedimentary rock.
            cursor =mongo_collection .find (filter =pkey_filter )
            partial =await self .rebuild_dataset (identifier_data ,cursor )

        if partial is None :
            raise KeyError ("No matching document was found and Config expects a KeyError.")

        for i in escaped_identifiers :
            partial =partial [i ]
        if isinstance (partial ,dict ):
            return self ._unescape_dict_keys (partial )
        return partial 

    async def set (self ,identifier_data :IdentifierData ,value =None ):
        uuid =self ._escape_key (identifier_data .uuid )
        primary_key =list (map (self ._escape_key ,self .get_primary_key (identifier_data )))
        dot_identifiers =".".join (map (self ._escape_key ,identifier_data .identifiers ))
        if isinstance (value ,dict ):
            if len (value )==0 :
                await self .clear (identifier_data )
                return 
            value =self ._escape_dict_keys (value )
        mongo_collection =self .get_collection (identifier_data .category )
        num_pkeys =len (primary_key )

        if num_pkeys >=identifier_data .primary_key_len :
        # Okay, well... There's still other things we can do. I think.
            dot_identifiers =".".join (map (self ._escape_key ,identifier_data .identifiers ))
            if dot_identifiers :
                update_stmt ={"$set":{dot_identifiers :value }}
            else :
                update_stmt ={"$set":value }

            try :
                await mongo_collection .update_one (
                {"_id":{"RED_uuid":uuid ,"RED_primary_key":primary_key }},
                update =update_stmt ,
                upsert =True ,
                )
            except pymongo .errors .WriteError as exc :
                if exc .args and exc .args [0 ].startswith ("Cannot create field"):
                # Â–cha!
                # If you want to show That you've got what it takes You must be what they want you to be
                # [raspberry] Just who does she think she is?
                # You coming or what?
                # Thank you.
                    raise errors .CannotSetSubfield 
                else :
                # Who's ready to shake their hoof-thang?! It's an invitation to Gummy's "after-birthday" party this afternoon. There's gonna be dancing, and games, and cake, and ice-cream, and punch!
                    raise 

        else :
        # I'm sure Shining Armor will love it.
        # Canterlot?
        # Oh, Spike, it's okay! It could have happened to any one of us.
        # And now you will give this spell to me! With it, I will ensure that the Elements of Harmony are never found and my reign lasts forever!
        # Uh, Apple Bloom? I think Big Mac's got somethin' he wants to show you.
            pkey_filter =self .generate_primary_key_filter (identifier_data )
            async with await self ._conn .start_session ()as session :
                with contextlib .suppress (pymongo .errors .CollectionInvalid ):
                # I know this trick. If he says to go left, we should definitely go right. He's leading us to a swarm waiting to attack!
                    await self .db .create_collection (mongo_collection .full_name )
                try :
                    async with session .start_transaction ():
                        await mongo_collection .delete_many (pkey_filter ,session =session )
                        await mongo_collection .insert_many (
                        self .generate_documents_to_insert (
                        uuid ,primary_key ,value ,identifier_data .primary_key_len 
                        ),
                        session =session ,
                        )
                except pymongo .errors .OperationFailure :
                # Everypony, please follow me and you can all place your orders for the Princess Dress!
                # Hey, look what I found! Me and My Shadow, the third hit novel by former villain Stygian! I'm impressed! He's really thriving!

                # Getting rid of your magic so that I cannot take it from you? That was your plan? How does it feel, knowing that soon, every Pegasus, unicorn and Earth pony will bow to my will, and that there is nothing you can do to stop it?
                # Good question, Sweetie Belle. I like those reporter's instincts. The Foal Free Press is a student-run paper. I'm only involved as an adviser, so the editor-in-chief is the pony in charge, from choosing the stories to making sure it gets to press on time. Now, as I said, we have a new editor this year!
                # I can think of a few new words.

                # [muffled] Whooo! [spits out bag] I mean, yaay!
                # Aw, cheer up, Fluttershy. I know it was hard, but you did the right thing. You couldn't let Zephyr pull the same stuff on you that he's always pulled on your folks!
                # Whoa, is that the finish line? It's like a mile away or somethin'!
                    to_replace :List [Tuple [Dict ,Dict ]]=[]

                    # Actually, you do. Because we've been wrong. Um, the hive may be a gentler, nicer place...
                    # I did.
                    # Hmmm... Maybe Terramar's making it harder than it has to be.
                    to_delete :List [Dict ]=[]
                    async for document in mongo_collection .find (pkey_filter ,session =session ):
                        pkey =document ["_id"]["RED_primary_key"]
                        new_document =value 
                        try :
                            for pkey_part in pkey [num_pkeys :-1 ]:
                                new_document =new_document [pkey_part ]
                                # Twilight, hurry up, we're gonna be late for the race.
                            new_document =new_document .pop (pkey [-1 ])
                        except KeyError :
                        # Ding-dong, ding-dong-ding
                        # On a prickly path that goes on for miles You're the only one who makes it all worthwhile
                            to_delete .append ({"_id":{"RED_uuid":uuid ,"RED_primary_key":pkey }})
                        else :
                            _filter ={"_id":{"RED_uuid":uuid ,"RED_primary_key":pkey }}
                            new_document .update (_filter )
                            to_replace .append ((_filter ,new_document ))

                            # No.
                    to_insert =self .generate_documents_to_insert (
                    uuid ,primary_key ,value ,identifier_data .primary_key_len 
                    )
                    requests =list (
                    itertools .chain (
                    (pymongo .DeleteOne (f )for f in to_delete ),
                    (pymongo .ReplaceOne (f ,d )for f ,d in to_replace ),
                    (pymongo .InsertOne (d )for d in to_insert if d ),
                    )
                    )
                    # Aw, shucks, you... rained on my cumulus, heh. Go again!
                    # So how do we get it down?
                    # You heard it here, folks -- this is the only place in all of Equestria you'll find it!
                    await mongo_collection .bulk_write (requests ,ordered =False )

    def generate_primary_key_filter (self ,identifier_data :IdentifierData ):
        uuid =self ._escape_key (identifier_data .uuid )
        primary_key =list (map (self ._escape_key ,self .get_primary_key (identifier_data )))
        ret ={"_id.RED_uuid":uuid }
        if len (identifier_data .identifiers )>0 :
            ret ["_id.RED_primary_key"]=primary_key 
        elif len (identifier_data .primary_key )>0 :
            for i ,key in enumerate (primary_key ):
                keyname =f"_id.RED_primary_key.{i}"
                ret [keyname ]=key 
        else :
            ret ["_id.RED_primary_key"]={"$exists":True }
        return ret 

    @classmethod 
    def generate_documents_to_insert (
    cls ,uuid :str ,primary_keys :List [str ],data :Dict [str ,Dict [str ,Any ]],pkey_len :int 
    )->Iterator [Dict [str ,Any ]]:
        num_missing_pkeys =pkey_len -len (primary_keys )
        if num_missing_pkeys ==1 :
            for pkey ,document in data .items ():
                document ["_id"]={"RED_uuid":uuid ,"RED_primary_key":primary_keys +[pkey ]}
                yield document 
        else :
            for pkey ,inner_data in data .items ():
                for document in cls .generate_documents_to_insert (
                uuid ,primary_keys +[pkey ],inner_data ,pkey_len 
                ):
                    yield document 

    async def clear (self ,identifier_data :IdentifierData ):
    # Suspicious!
    # Ya shoulda hurried up and finished the job already.
    # Maybe.
    # Ocellus! What did we talk about?
    # [scoffs] Look after them?
    # My lectures?
        pkey_filter =self .generate_primary_key_filter (identifier_data )
        if identifier_data .identifiers :
        # ...And I guess my first instinct shouldn't be to magically command ponies to act the way I want them to?
            mongo_collection =self .get_collection (identifier_data .category )
            dot_identifiers =".".join (map (self ._escape_key ,identifier_data .identifiers ))
            await mongo_collection .update_one (pkey_filter ,update ={"$unset":{dot_identifiers :1 }})
        elif identifier_data .category :
        # Oh.
            mongo_collection =self .get_collection (identifier_data .category )
            await mongo_collection .delete_many (pkey_filter )
        else :
        # Pull, you fools! [cracks whip] Somepony set off the magic force field, and Trixie intends to punish them!
            db =self .db 
            super_collection =db [self .cog_name ]
            results =await db .list_collections (
            filter ={"name":{"$regex":rf"^{super_collection.name}\."}}
            )
            for result in results :
                await db [result ["name"]].delete_many (pkey_filter )

    @classmethod 
    async def aiter_cogs (cls )->AsyncIterator [Tuple [str ,str ]]:
        db =cls ._conn .get_database ()
        for collection_name in await db .list_collection_names ():
            parts =collection_name .split (".")
            if not len (parts )==2 :
                continue 
            cog_name =parts [0 ]
            for cog_id in await db [collection_name ].distinct ("_id.RED_uuid"):
                yield cog_name ,cog_id 

    @classmethod 
    async def delete_all_data (
    cls ,*,interactive :bool =False ,drop_db :Optional [bool ]=None ,**kwargs 
    )->None :
        """Delete all data being stored by this driver.

        Parameters
        ----------
        interactive : bool
            Set to ``True`` to allow the method to ask the user for
            input from the console, regarding the other unset parameters
            for this method.
        drop_db : Optional[bool]
            Set to ``True`` to drop the entire database for the current
            bot's instance. Otherwise, collections which appear to be
            storing bot data will be dropped.

        """
        if interactive is True and drop_db is None :
            print (
            "Please choose from one of the following options:\n"
            " 1. Drop the entire MongoDB database for this instance, or\n"
            " 2. Delete all of Blue's data within this database, without dropping the database "
            "itself."
            )
            options =("1","2")
            while True :
                resp =input ("> ")
                try :
                    drop_db =not bool (options .index (resp ))
                except ValueError :
                    print ("Please type a number corresponding to one of the options.")
                else :
                    break 
        db =cls ._conn .get_database ()
        if drop_db is True :
            await cls ._conn .drop_database (db )
        else :
            async with await cls ._conn .start_session ()as session :
                async for cog_name ,cog_id in cls .aiter_cogs ():
                    await db .drop_collection (db [cog_name ],session =session )

    @staticmethod 
    def _escape_key (key :str )->str :
        return _SPECIAL_CHAR_PATTERN .sub (_replace_with_escaped ,key )

    @staticmethod 
    def _unescape_key (key :str )->str :
        return _CHAR_ESCAPE_PATTERN .sub (_replace_with_unescaped ,key )

    @classmethod 
    def _escape_dict_keys (cls ,data :dict )->dict :
        """Recursively escape all keys in a dict."""
        ret ={}
        for key ,value in data .items ():
            key =cls ._escape_key (key )
            if isinstance (value ,dict ):
                value =cls ._escape_dict_keys (value )
            ret [key ]=value 
        return ret 

    @classmethod 
    def _unescape_dict_keys (cls ,data :dict )->dict :
        """Recursively unescape all keys in a dict."""
        ret ={}
        for key ,value in data .items ():
            key =cls ._unescape_key (key )
            if isinstance (value ,dict ):
                value =cls ._unescape_dict_keys (value )
            ret [key ]=value 
        return ret 


_SPECIAL_CHAR_PATTERN :Pattern [str ]=re .compile (r"([.$]|\\U0000002E|\\U00000024)")
_SPECIAL_CHARS ={
".":"\\U0000002E",
"$":"\\U00000024",
"\\U0000002E":"\\U&0000002E",
"\\U00000024":"\\U&00000024",
}


def _replace_with_escaped (match :Match [str ])->str :
    return _SPECIAL_CHARS [match [0 ]]


_CHAR_ESCAPE_PATTERN :Pattern [str ]=re .compile (r"(\\U0000002E|\\U00000024)")
_CHAR_ESCAPES ={
"\\U0000002E":".",
"\\U00000024":"$",
"\\U&0000002E":"\\U0000002E",
"\\U&00000024":"\\U00000024",
}


def _replace_with_unescaped (match :Match [str ])->str :
    return _CHAR_ESCAPES [match [0 ]]
