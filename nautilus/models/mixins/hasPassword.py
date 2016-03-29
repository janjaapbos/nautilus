# local imports
from ..models import BaseModel
from ..fields import PasswordField

class HasPassword(BaseModel):
    password = PasswordField()
