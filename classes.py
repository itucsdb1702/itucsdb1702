import psycopg2 as dbapi2
from flask import current_app as app
from flask_login import UserMixin
from flask import flash
from flask_login import login_manager, login_user, logout_user
from passlib.apps import custom_app_context as pwd_context
from flask_login.login_manager import LoginManager
import requests

class User(UserMixin):
    def __init__(self, username, email, password):
        self.username = username
        self.password = password
        self.email = email

    def get_id(self):
        with dbapi2._connect(app.config['dsn']) as connection:

            cursor = connection.cursor()

            query = "SELECT ID FROM USERS WHERE (USERNAME = %s)"

            cursor.execute(query, (self.username,))

            user = cursor.fetchone()
            if user is None:
                return
            else:
                return self.username

    def get_user_id(self):
        with dbapi2._connect(app.config['dsn']) as connection:

            cursor = connection.cursor()

            query = "SELECT ID FROM USERS WHERE (USERNAME = %s)"

            cursor.execute(query, (self.username,))

            userid = cursor.fetchone()
            if userid is None:
                return
            else:
                return userid

    def get_posts(self):
        with dbapi2._connect(app.config['dsn']) as connection:

            cursor = connection.cursor()

            query = """SELECT p.POST_ID, TITLE, COMMENTS FROM
                            USERS u INNER JOIN POSTS p ON (u.ID = p.USER_ID)
                            INNER JOIN MOVIES m ON (m.MOVIEID = p.MOVIE_ID)
                        WHERE (USERNAME = %s)"""

            cursor.execute(query, (self.username,))
            posts = []
            for postid in cursor:
                posts.append(postid)

            connection.commit()

            return posts

    def get_following_users_by_userid(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """SELECT ID, USERNAME, EMAIL FROM USERS u
                               INNER JOIN FOLLOWERS f ON (u.ID = f.FOLLOWED_USER_ID)
                               WHERE (f.FOLLOWING_USER_ID = %s) """

                    userid = self.get_user_id()
                    cursor.execute(query, (userid,))

                    users = []
                    for user in cursor:
                        users.append(user)

                    connection.commit()

                    return users
                
    def get_followed_users_by_userid(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """SELECT ID, USERNAME, EMAIL FROM USERS u
                               INNER JOIN FOLLOWERS f ON (u.ID = f.FOLLOWING_USER_ID)
                               WHERE (f.FOLLOWED_USER_ID = %s) """

                    userid = self.get_user_id()
                    cursor.execute(query, (userid,))

                    users = []
                    for user in cursor:
                        users.append(user)

                    connection.commit()

                    return users


    def is_active(self):
        # Here you should write whatever the code is
        # that checks the database if your user is active
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

class UserList:
    def __init__(self):
        self.last_user_id = None

    def add_user(self,newuser):
        with dbapi2.connect(app.config['dsn']) as connection:
            cursor = connection.cursor()
            query = """INSERT INTO USERS (USERNAME, EMAIL, PASSWORD) VALUES (%s, %s, %s)"""
            cursor.execute(query, (newuser.username, newuser.email, newuser.password))
            connection.commit()
            cursor.close()

    def verify(self,username,passw):
        with dbapi2.connect(app.config['dsn']) as connection:
            cursor = connection.cursor()
            query = "SELECT USERNAME, PASSWORD FROM USERS WHERE (USERNAME = %s)"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            if user is not None:
                if pwd_context.verify(passw,user[1]):
                    return 0
                else:
                    return -1
            else:
                return -1

class Movie:
    def __init__(self, title, year, score, votes, imdb_url):
        self.title = title
        self.year = year
        self.score = score
        self.votes = votes
        self.imdb_url = imdb_url

    def search_movie_in_db(self):
        with dbapi2.connect(app.config['dsn']) as connection:
            cursor = connection.cursor()
            query = "SELECT MOVIEID FROM MOVIES WHERE (TITLE = %s)"
            cursor.execute(query, (self.title, ))
            movie = cursor.fetchone()

            if movie is not None:
                return movie
            else:
                return -1

    def getscore_in_movie_db(self, movieid):
        with dbapi2.connect(app.config['dsn']) as connection:
            cursor = connection.cursor()
            query = "SELECT SCORE FROM MOVIES WHERE (MOVIEID = %s)"
            cursor.execute(query, (movieid, ))
            movie = cursor.fetchone()

            if movie is not None:
                return movie
            else:
                return -1

    def getvotes_in_movie_db(self, movieid):
        with dbapi2.connect(app.config['dsn']) as connection:
            cursor = connection.cursor()
            query = "SELECT VOTES FROM MOVIES WHERE (MOVIEID = %s)"
            cursor.execute(query, (movieid, ))
            movie = cursor.fetchone()

            if movie is not None:
                return movie
            else:
                return -1

    def verify_movie_from_api(self):

        title = self.title.replace(' ', '+')
        url = "http://www.omdbapi.com/?apikey=e5ccb3ca&t="+ self.title
        response = requests.get(url).json()

        if(response['Response'] == "False"):
            return -1

        else:
            title = response['Title']
            year = response['Year']
            votes = 1
            imdb_url = "http://www.imdb.com/title/" + response['imdbID']

            movie = Movie(title, year, "", votes, imdb_url)

            return movie

    def add_movie_to_db(self):
        with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """INSERT INTO MOVIES (TITLE, YEAR, SCORE, VOTES, IMDB_URL)
                    VALUES (%s, %s, %s, %s, %s)"""

                    cursor.execute(query, (self.title, self.year, self.score, self.votes, self.imdb_url))
                    connection.commit()

    def update_votes_and_score(self, movieid, score, votes):
        with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """UPDATE MOVIES
                            SET SCORE = %s, VOTES= %s
                            WHERE MOVIEID = %s;"""

                    cursor.execute(query, (score, votes, movieid))
                    connection.commit()

class Post:
    def __init__(self, userid, movieid, comment):
        self.userid = userid
        self.movieid = movieid
        self.comment = comment

    def add_post_to_db(self):
        with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """INSERT INTO POSTS (USER_ID, MOVIE_ID, COMMENTS)
                    VALUES (%s, %s, %s)"""

                    cursor.execute(query, (self.userid, self.movieid, self.comment))
                    connection.commit()

    def delete_post_from_db(self):
        with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """DELETE FROM POSTS WHERE (USER_ID = %s) AND
                                                        (MOVIE_ID = %s) AND
                                                        (COMMENTS = %s)
                            """

                    cursor.execute(query, (self.userid, self.movieid, self.comment))
                    connection.commit()

class WatchedList:
    def __init__(self, username, movieid, score):
        self.username = username
        self.movieid = movieid
        self.score = score

    def add_movie_user_pair(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """INSERT INTO WATCHEDLIST (USERNAME, MOVIEID, SCORE)
                    VALUES (%s, %s, %s)"""

                    cursor.execute(query, (self.username, self.movieid, self.score))
                    connection.commit()
    def existsInWatchedList(self):
         with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """SELECT SCORE FROM WATCHEDLIST WHERE ((USERNAME = %s) AND (MOVIEID = %s)) """

                    cursor.execute(query, (self.username, self.movieid))
                    score = cursor.fetchone()

                    if score is None:
                        return -1
                    else:
                        return score
  
    def delete_from_watched_list(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """DELETE FROM WATCHEDLIST
                                WHERE((USERNAME = %s) AND (MOVIEID = %s))"""

                    cursor.execute(query, (self.username, self.movieid))
                    connection.commit()
                    
    def updateScoreOfWatchedMovie(self):
         with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """UPDATE WATCHEDLIST
                                SET SCORE =%s
                                WHERE ((USERNAME = %s) AND (MOVIEID = %s))"""

                    cursor.execute(query, (self.score, self.username, self.movieid))
                    connection.commit()
class FollowerPair:
    def __init__(self, following_id, followed_id):
        self.following_id = following_id
        self.followed_id = followed_id

    def new_follow(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """INSERT INTO FOLLOWERS (FOLLOWING_USER_ID, FOLLOWED_USER_ID)
                    VALUES (%s, %s)"""

                    cursor.execute(query, (self.following_id, self.followed_id))
                    connection.commit()

    def unfollow(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """DELETE FROM FOLLOWERS
                                WHERE((FOLLOWING_USER_ID = %s) AND (FOLLOWED_USER_ID = %s))"""

                    cursor.execute(query, (self.following_id, self.followed_id,))
                    connection.commit()

    def exists(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """SELECT FRIENDSHIP_ID FROM FOLLOWERS
                                WHERE((FOLLOWING_USER_ID = %s) AND (FOLLOWED_USER_ID = %s))"""

                    cursor.execute(query, (self.following_id, self.followed_id))
                    pair = cursor.fetchone()

                    connection.commit()

                    if pair is None:
                        return False
                    else:
                        return True

class MovieList:
    def __init__(self, user_id, movie_id, list_name):
        self.user_id = user_id
        self.movie_id = movie_id
        self.list_name = list_name

    def add_movie(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """INSERT INTO MOVIELIST (USER_ID, MOVIE_ID, LIST_NAME)
                    VALUES (%s, %s, %s)"""

                    cursor.execute(query, (self.user_id, self.movie_id, self.list_name))
                    connection.commit()

    def delete_list(self):
         with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """DELETE FROM MOVIELIST WHERE ((LIST_NAME = %s) AND (USER_ID = %s))"""

                    cursor.execute(query, (self.list_name, self.user_id,))
                    connection.commit()

    def exists(self):
            with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """SELECT LIST_ID FROM MOVIELIST
                                WHERE((LIST_NAME = %s) AND (MOVIE_ID = %s) AND (USER_ID = %s))"""

                    cursor.execute(query, (self.list_name, self.movie_id, self.user_id, ))
                    name = cursor.fetchone()

                    connection.commit()

                    if name is None:
                        return self
                    else:
                        return 1

    def removeMovieFromList(self):
        with dbapi2.connect(app.config['dsn']) as connection:
                    cursor = connection.cursor()
                    query = """DELETE FROM MOVIELIST WHERE ((LIST_NAME = %s) AND (USER_ID = %s) AND (MOVIE_ID = %s))"""

                    cursor.execute(query, (self.list_name, self.user_id, self.movie_id,))
                    connection.commit()

class Series:
    def add_series(TITLE, STARTYEAR, ENDYEAR, SCORE, VOTES,PICTURE, DESCRIPTION):
        with dbapi2.connect(dsn) as connection:
            try:
                cursor = connection.cursor()
                state= """INSERT INTO SERIES (TITLE, STARTYEAR, ENDYEAR, SCORE, VOTES,PICTURE, DESCRIPTION) VALUES(%s,%s,%s,%s,%s,%s,%s)"""
                cursor.execute(state)
                connection.commit()
                cursor.close()
            except dbapi2.DatabaseError as e:
                connection.rollback()

    def delete_series(ID):
        with dbapi2.connect(dsn) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""DELETE FROM SERIES WHERE ID = %s""", (int(ID),))
                connection.commit()
            except dbapi2.DatabaseError as e:
                connection.rollback()

    def update_series(ID, TITLE, STARTYEAR, ENDYEAR, SCORE, VOTES,PICTURE, DESCRIPTION):
        with dbapi2.connect(dsn) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""UPDATE SERIES SET TITLE = '%s', STARTYEAR = '%s', ENDYEAR = '%s', SCORE = '%s', VOTES = '%s', PICTURE = '%s', DESCRIPTION = '%s' WHERE ID = %d"""
                               % (TITLE, STARTYEAR, ENDYEAR, SCORE, VOTES,PICTURE, DESCRIPTION,int(ID)))
                connection.commit()
            except dbapi2.DatabaseError as e:
                connection.rollback()