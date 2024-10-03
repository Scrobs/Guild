# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import func
from .models import db, User, Game, votes
from .forms import LoginForm, PasswordResetForm, VoteForm  

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Order games by number of voters descending
    games = Game.query.outerjoin(votes).group_by(Game.id).order_by(func.count(votes.c.user_id).desc()).all()
    
    # Create a dictionary of VoteForm instances keyed by game ID
    vote_forms = {game.id: VoteForm(prefix=str(game.id)) for game in games}
    
    return render_template('games.html', games=games, vote_forms=vote_forms)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.check_password(user.bgg_username):
                flash('Please reset your password.')
                return redirect(url_for('main.reset_password'))
            flash('Logged in successfully.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)  
    
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@main.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = PasswordResetForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated.')
        return redirect(url_for('main.index'))
    return render_template('reset_password.html', form=form)

@main.route('/vote/<int:game_id>', methods=['POST'])
@login_required
def vote(game_id):
    game = Game.query.get_or_404(game_id)
    
    # Instantiate the VoteForm with the correct prefix
    form = VoteForm(prefix=str(game_id))
    
    if form.validate_on_submit():
        if game in current_user.votes:
            current_user.votes.remove(game)
            flash(f'Your vote for "{game.name}" has been removed.')
        else:
            if current_user.vote_count() >= 3:
                flash('You have reached the maximum number of votes.')
                return redirect(url_for('main.index'))
            current_user.votes.append(game)
            flash(f'You have voted for "{game.name}".')
        db.session.commit()
    else:
        flash('Invalid vote submission.')
    
    return redirect(url_for('main.index'))
