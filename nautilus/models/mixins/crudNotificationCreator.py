# external imports
from sqlalchemy import event
# local imports
from nautilus.network import dispatch_action

class CRUDNotificationCreator:
    """
        This mixin class provides basic crus event publishing when the model
        is mutated, following nautilus conventions.
    """


    nautilus_base = True # required to prevent self-application on creation

    @classmethod
    def add_listener(cls, db_event, action_type):
        # on event, dispatch the appropriate action
        @event.listens_for(cls, db_event)
        def dispatchCRUDAction(mapper, connection, target):
            """ notifies the network of the new user model """
            dispatch_action(
                action_type='{}_{}'.format(cls.__name__.lower(), type),
                payload=target.__json__(),
            )


    @classmethod
    def onCreation(cls):
        # perform the intended behavior
        super().onCreation()
        # add the crud action emitters
        cls.add_listener('after_insert', 'create_success')
        cls.add_listener('after_delete', 'delete_success')
        cls.add_listener('after_update', 'update_success')
