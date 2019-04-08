from flask import Flask , render_template,session,redirect,request, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
mysql = connectToMySQL('wall_db')
app.secret_key = 'bla'

@app.route('/')
def landing():
    if 'first_name' not in session:
        session['first_name']=''
        session['last_name']=''
        session['email']=''
    session['randomval'] = mysql.query_db('SELECT email from users where email="1";')
    return render_template("landing.html")
@app.route('/process', methods=['post'])
def register():
    session['first_name']=''
    session['last_name']=''
    session['email']=''
    count = 0
    # query='SELECT email from users where email="shxwnpcw@hotmail.com";'
    # print(mysql.query_db(query))
    # users =
    
    # print(randomval)
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
    for i in request.form['email']:
        if i == '@':
            count+=1
    if len(request.form['firstname']) < 2 or  any(i.isdigit() for i in request.form['firstname'])== True:
        flash("First name requires more than 2 charaters and can only contain letters", 'first_name_error')
    elif len(request.form['lastname']) < 2 or  any(i.isdigit() for i in request.form['firstname'])== True:
        flash("Last name requires more than 2 charaters and can only contain letters", 'last_name_error')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'email_error')
    elif mysql.query_db('SELECT email from users where email="'+request.form['email']+'";') != session['randomval']:
        flash("Email already in use!",'email_error')
    elif any(i.isdigit() for i in request.form['password']) ==False or len(request.form['password']) < 6:
        flash("Password contain at least 1 number and must be longer than 6 charaters","password_error")
    elif request.form['password'] != request.form['cmpassword']:
        flash('Passwords do not match!','confirm_pass_error')
    else:
        data = {
            'first_name':request.form['firstname'],
            'last_name': request.form['lastname'],
            'email'     :request.form['email'],
            'password'  : bcrypt.generate_password_hash(request.form['password'])
        }

        flash('Successful Registration!', 'success')
        query = "INSERT INTO users (first_name, last_name, email, pw_hash, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s,%(password)s, NOW(), NOW());"
        # print(query)
        mysql.query_db(query, data)
        query='SELECT id from users where email = %(email)s;'
        data = {
            'email':request.form['email']
        } 
        
        user_id = mysql.query_db(query,data)
        print(user_id)
        # user_id = user_id
        session['logged_user_id'] = user_id[0]['id']
        return redirect('/home_page')
    session['first_name']= request.form['firstname']
    session['last_name']= request.form['lastname']
    session['email']= request.form['email']
    return redirect("/")

@app.route('/login', methods=['post'])
def login():
    query='SELECT * from users where email = %(email)s;'
    data = {
        'email':request.form['email']
    }
    session['randomval'] = mysql.query_db('SELECT email from users where email="1";')
    users =mysql.query_db(query,data)
    if users ==  session['randomval']:
        flash('email does not exist!','loginEmailError')
        return redirect('/')
    print(users)
    for i in users:
        print(i)
        print('--------------------------------------------')
        if i['email'] == request.form['email'] and bcrypt.check_password_hash(i['pw_hash'], request.form['password']) ==True:
            session['logged_user_id'] = i['id']
            print("logged in!")
            return redirect("/home_page")
        else:
            print('failed to log in')
            flash('You could not be logged in','failedLogin')
            return redirect('/')
    

@app.route('/home_page')
def homePage():
    # print(session['logged_user_id'])
    user_id = str(session['logged_user_id']) #gets current users id
    query='SELECT * from users where id = %(id)s;'
    data = {
        'id':user_id
    }
    session['user'] =mysql.query_db(query,data) #getting all the information for current user
    query='select * from messages left join users on users.id = messages.users_id_sent_from where users_id_sent_to = %(id)s;'
    session['data'] =mysql.query_db(query,data) #getting all the data for both tables and storing it intodata
    query='select * from messages left join users on users.id = messages.users_id_sent_from where users_id_sent_from = %(id)s;'
    messSent =mysql.query_db(query,data)
    messSent = len(messSent)
    print(session['data'])
    currentmessages = len(session['data'])      #passing in the data
    query= 'select id, first_name from users where id not in (%(id)s);'
    otherusers=mysql.query_db(query,data)
    # print('------------------------------------------------------------')

    # print(session['data'][0]['id'])
    return render_template('homepage.html', numMes = currentmessages,otherusers=otherusers, messSent = messSent)

@app.route('/messages', methods=['post'])
def messages():

    data = {
        'content':request.form['message'],
        'users_id_sent_from': request.form['sendID'],
        'users_id_sent_to': request.form['reciverID']

    }
    query = "INSERT INTO messages (content, created_at, updated_at, users_id_sent_from,users_id_sent_to) VALUES (%(content)s, NOW(), NOW(), %(users_id_sent_from)s,%(users_id_sent_to)s);"

    mysql.query_db(query, data)
    return redirect('/home_page')
@app.route('/logout')
def logout():
    print('session cleared')
    session.clear

    return redirect('/')
@app.route('/delete', methods=['post'])
def delete():
    
    query ='DELETE from messages where id = %(id)s'
    data = {
        'id':request.form['messageID']
    }
    print(request.form['messageID'])
    print(data['id'])
    answer = mysql.query_db(query,data)
    print(answer)
    return redirect('/home_page')

if __name__ == "__main__":
    app.run(debug=True)