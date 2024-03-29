from models.base_model import BaseModel
import peewee as pw
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re 
from flask_login import UserMixin
from playhouse.hybrid import hybrid_property 
from models.user import User 


class Image(UserMixin, BaseModel):
    title = pw.CharField(null=False)
    image_url = pw.TextField(null=False)
    description = pw.CharField(null=False, max_length = 500)
    user = pw.ForeignKeyField(User, backref = "users")
    date_posted = pw.DateField(default = datetime.datetime.now )
    likes = pw.IntegerField(default = 0)
    donation = pw.IntegerField(default = 0)


    @hybrid_property
    def full_image_path(self):
        return AWS_S3_DOMAIN + self.image_path 