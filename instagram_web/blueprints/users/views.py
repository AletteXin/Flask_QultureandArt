from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from models import * 
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.user import User 
import re
from flask_login import login_user, login_required
from instagram_web.util.helpers import upload_file_to_s3
from app import *
from models.images import Image
from peewee import prefetch 
from models.follow import Follow


users_blueprint = Blueprint('users',
                            __name__,
                            template_folder='templates')


@users_blueprint.route('/new', methods=['GET'])
def new():
    return render_template('/users/new.html')


@users_blueprint.route('/create-new', methods=['POST'])
def create():
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    reenter_password = request.form['reenter_password']
    email = request.form['email']
    birth_date = request.form['birth_date']

    if password != reenter_password:
        flash("Passwords do not match. Please reenter details.")

    new_user = User(name = name, username=username, password = password, email = email, birth_date = birth_date)

    if new_user.save():
        user = User.get_or_none(User.username == username)
        session['user_id'] = user.id
        show_profilepic = user.image_path
        show_description = user.description
        login_user(user)
        return redirect(url_for('users.show', username = username, show_profilepic = show_profilepic, 
        show_username = username, show_description = show_description))
    
    else:
        return redirect('/users/new')
    

@users_blueprint.route('/profile/<show_username>', methods=["GET"])
@login_required
def show(show_username):
    
    if session.get('user_id'):
        user = User.get_or_none(User.id == session["user_id"])
        if user:
            username = user.username
        else:
            username = None
        
        show_user = User.get_or_none(User.username == show_username)
        if show_user:
            show_username = show_user.username
            show_profilepic = show_user.image_path
            show_description = show_user.description
            show_privacy = show_user.privacy 
            images = Image.select().where(Image.user_id == show_user.id).order_by(Image.date_posted.desc())
            already_following = Follow.get_or_none(Follow.follower == user and Follow.idol == show_user)

            return render_template('/users/profile.html', username = username, show_profilepic = show_profilepic, 
            show_privacy = show_privacy, show_username = show_username, show_description = show_description, 
            already_following = already_following, images = images)

        else:
            return redirect('/404.html')
        
        
    else:
        return redirect (url_for('login.new'))


@users_blueprint.route('/', methods=["GET"])
def index():
    return redirect('/users/new')


@users_blueprint.route('/edit', methods=['GET'])
@login_required
def edit():
    user = User.get_or_none(User.id == session['user_id'])
    if user:
        username = user.username
    else:
        username = None 
    return render_template("/users/edit.html", username = username, show_username = username )


@users_blueprint.route('/update/<field>', methods=['POST'])
@login_required
def update(field):
    if session.get('user_id'):
        user = User.get_or_none(User.id == session['user_id'])
        if user:
            new_info = request.form[field]
            
            if field == "email":
                email_existing = User.get_or_none(User.email == new_info)
                if email_existing:
                    flash("There is an existing account associated with this email.")
                    return redirect (url_for('users.edit'))
            
            if field == "username":
                existing_username = User.get_or_none(User.username == new_info)
                if existing_username:
                    flash("Sadly, this username has been taken. Please choose another.")
                    return redirect (url_for('users.edit'))
            
            if field == "password":
                reenter_password = request.form['reenter_password']

                if new_info != reenter_password:
                    flash("Passwords do not match. Please reenter details.")
                    return redirect (url_for('users.edit'))

            if field == "privacy":
                if new_info == "Public":
                    new_info = "1"
                else:
                    new_info = "0"

            setattr(user, field, new_info)
            user.save()
            
            # update = User.update(**{field: new_info}).where(User.id == session.get('user_id'))
            # update.execute()

            flash("Your info has been updated.")
        else:
            flash("An error occured, please try again.")
        return redirect (url_for('users.edit'))

    else:
        flash("An error occured, please try again.")
        return redirect (url_for('users.edit'))


@users_blueprint.route('/upload')
@login_required
def upload():
    user = User.get_or_none(User.id == session['user_id'])
    if user:
        username = user.username
    else:
        username = None 

    return render_template ("/users/upload.html", username = username)


@users_blueprint.route('/upload/profilepic/', methods=['POST'])
@login_required
def newpic():
    user = User.get_or_none(User.id == session['user_id'])
    if user:
        username = user.username
    else:
        username = None 
    
    if user:
        
        print(request.files["profilepic"])

        if "profilepic" not in request.files:
            flash ("No profilepic key in request.files.")
            return redirect(url_for('users.upload', username = username))

        file = request.files["profilepic"]

        if file.filename == "":
            flash("Please attach a file.")
            return redirect(url_for('users.upload', username = username))

        file.filename = secure_filename(file.filename)
        print(file.filename)
        image_path = upload_file_to_s3(file, app.config["S3_BUCKET"])

        print(image_path)

        user.image_path = image_path 

        if user.save():
            flash("Image uploaded successfully!")
            return redirect(url_for('users.upload', username = username))
        else:
            flash("Image upload unsuccessful. Please try again.")
            return redirect(url_for('users.upload', username = usermame))
    
    return redirect(url_for('users.upload', username = usermame))





@users_blueprint.route('/<show_username>/follow')
@login_required
def follow(show_username):
    
    user = User.get_or_none(User.id == session['user_id'])
    username = user.username
    follower = user
    idol = User.get_or_none(User.username == show_username)
    already_following = Follow.get_or_none(Follow.follower_id == follower and Follow.idol_id == idol)

    if already_following:
        already_following.delete_instance()
        flash(f"You are no longer following {show_username}")
        return redirect(url_for('users.show', username = username, show_username = show_username))
    
    elif Follow.create(idol = idol, follower = user):
        flash(f"Congratulations! You are now following {show_username}")
        return redirect(url_for('users.show', username = username, show_username = show_username))

    else:
        return redirect('/404.html')

# user = User.select().first()
# idols = User.select().join(Follow, on = Follow.follower_id == User.id).where(Follow.idol == user)
# print([i for i in followers])


# @users_blueprint.route('/approve')
# @login_required
# def approve():

    