#Flask app project by Ash_360
from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, TextAreaField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.debug = True

#Config mySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Initialize MySQL
mysql = MySQL(app)



#Articles = Articles()
#Main page
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/article/<string:id>/')
def article(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    #Fetch one article
    article = cur.fetchone()
    return render_template('article.html',article=article)

#Register class for wtforms
class RegisterForm(Form):
    name = StringField('Name', validators=[validators.input_required(),validators.Length(min=1, max=50)])
    username = StringField('Username', validators=[validators.Length(min=4, max=25)])
    email = StringField('Email', validators=[validators.input_required(),validators.Length(min=6, max=50)])
    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

#register route for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        #form.name.data is used due to wtforms otherwise use only request.form.['name_field']
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create DictCursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close Conncection
        cur.close()

        flash('You are registered and can login!','success')

        return redirect(url_for('login'))
    return render_template('register.html',form = form)

#User login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        #Get user by Username
        result  = cur.execute("SELECT * FROM users WHERE username = %s",[username])

        if result > 0:
            #Get stored hash password
            data = cur.fetchone()
            #Since we are using our cursor as a dictionary thats why it returns a dictionary00
            password = data['password']

            #Comparing password hashes
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                app.logger.info('PASSWORD MATCHED')
                flash('You are now logged in.','success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid login"
                app.logger.info('PASSWORD NOT MATCHED')
                return render_template('login.html', error = error)
            #Close DB Conncection
            cur.close()

        else:
            error = "Username not found"
            return render_template('login.html', error = error)

    return render_template('login.html')
#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please login",'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/articles')
@is_logged_in
def articles():
    #Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)

        #Close sql connection
        cur.close()


#Log out
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('Successully logged out','success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    #Close sql connection
    cur.close()

    #return render_template('dashboard.html')

#Add Articles Form Class
class ArticleForm(Form):
    title = StringField('Title', validators=[validators.input_required(),validators.Length(min=1, max=200)])
    body = TextAreaField('Body', validators=[validators.Length(min=30)],  render_kw={"rows": 8, "cols": 11})

# Add Articles
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create Cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit
        mysql.connection.commit()

        #Close
        cur.close()

        #Flash message
        flash("Articles created successully", 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Articles
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    #Get user by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    #Get form
    form = ArticleForm(request.form)

    #Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create Cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))

        # Commit
        mysql.connection.commit()

        #Close
        cur.close()

        #Flash message
        flash("Articles updated successully!", 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

#Delete Articles
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    #Create Cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    #Commit
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article deleted successfully!', 'success')

    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    #secret key is defined for the session
    app.secret_key = 'secret123'
    app.run()
