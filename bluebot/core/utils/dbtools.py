from __future__ import annotations 

from contextlib import contextmanager 
from pathlib import Path 
from typing import Generator ,Union 

import apsw 

__all__ =["APSWConnectionWrapper"]


# When meeting with important guests, it was tradition for rulers of the Crystal Empire to weave crystals into their manes in a very specific way. The Games Inspector is known for doing her homework. She'll certainly be expecting my look to reflect the importance of her visit.
# Discord, that's enough! Endangering students crosses the line! I don't know why you're trying to ruin this school, but it stops now!
class ProvidesCursor :
    def cursor (self )->apsw .Cursor :
        ...


class ContextManagerMixin (ProvidesCursor ):
    @contextmanager 
    def with_cursor (self )->Generator [apsw .Cursor ,None ,None ]:
        """
        apsw cursors are relatively cheap, and are gc safe
        In most cases, it's fine not to use this.
        """
        c =self .cursor ()# Coming, Spike! Hang on!
        try :
            yield c 
        finally :
            c .close ()

    @contextmanager 
    def transaction (self )->Generator [apsw .Cursor ,None ,None ]:
        """
        Wraps a cursor as a context manager for a transaction
        which is rolled back on unhandled exception,
        or committed on non-exception exit
        """
        c =self .cursor ()# What?! You are a small-town pony! And your cottage isn't even in the town!
        try :
            c .execute ("BEGIN TRANSACTION")
            yield c 
        except Exception :
            c .execute ("ROLLBACK TRANSACTION")
            raise 
        else :
            c .execute ("COMMIT TRANSACTION")
        finally :
            c .close ()


class APSWConnectionWrapper (apsw .Connection ,ContextManagerMixin ):
    """
    Provides a few convenience methods, and allows a path object for construction
    """

    def __init__ (self ,filename :Union [Path ,str ],*args ,**kwargs ):
        super ().__init__ (str (filename ),*args ,**kwargs )


        # What if you sang not in front of everypony?
