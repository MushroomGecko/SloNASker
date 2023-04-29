import sys
import zipfile
from flask import Flask, render_template, request, send_file, make_response, session, redirect
from werkzeug.utils import secure_filename
import os
import json
import hashlib
import random

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "files/"
app.config["SECRET_KEY"] = os.urandom(random.randrange(4092))


@app.route('/', methods=['GET', 'POST'])
def index():
    # if os.path.exists("data.zip"):
    # os.remove("data.zip")

    # Gets name of every file in /files
    fNames = [x.name for x in os.scandir(app.config['UPLOAD_FOLDER'] + "public/")]

    if request.method == "POST":
        uploaded_files = request.files.getlist('file_upload')
        downloaded_files = request.form.getlist('file_download')
        print("Uploaded:", uploaded_files)
        print("Downloaded:", downloaded_files)

        # Handles file uploads
        for f in uploaded_files:
            name = secure_filename(f.filename)
            if name != "":
                while name in fNames:  # Handles file duplicates
                    name = name[0:name.rfind('.')] + "-" + name[name.rfind('.'):len(name)]
                f.save(app.config['UPLOAD_FOLDER'] + "public/" + name)

        # Handles file downloads
        if len(downloaded_files) > 1:  # If user tries to download more than one file
            with zipfile.ZipFile('public' + '_' + 'data.zip', 'w') as f:
                for file in downloaded_files:
                    f.write(app.config['UPLOAD_FOLDER'] + "public/" + file)
            return send_file('public' + '_' + 'data.zip', as_attachment=True)
        elif len(downloaded_files) == 1:  # If user tries to download exactly 1 file
            return send_file(app.config['UPLOAD_FOLDER'] + "public/" + downloaded_files[0], as_attachment=True)
    return render_template('index.html', fNames=fNames)

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == "POST":
        # Get user inputs
        username = str(request.form.get('username')).lower()
        password = str(request.form.get('password'))

        fNames = [x.name for x in os.scandir(app.config['UPLOAD_FOLDER'])]
        if username in fNames:
            print("Duplicate name")
            return render_template('signup.html')
        if len(password) > 64:
            print("Password too long")
            return render_template('signup.html')
        else:
            print("Success")
            session["username"] = username
            os.mkdir(app.config['UPLOAD_FOLDER'] + username)


            with open('users.json') as fp:
                data = json.load(fp)
            salt_file = open("salt.txt", 'r')
            salt = salt_file.readlines()[0]
            salt_file.close()
            data.append({
                "username": username,
                "password": hashlib.sha512((password + salt).encode('UTF-8')).hexdigest()
            })

            with open('users.json', 'w') as json_file:
                json.dump(data, json_file, indent=4, separators=(',', ': '))
            return redirect('/personal')
    return render_template('signup.html')

@app.route('/personal', methods=['GET', 'POST'])
def personal_page():
    # Handle request
    if request.method == "POST":

        # Get user inputs
        username = str(request.form.get('username')).lower()
        password = str(request.form.get('password'))
        uploaded_files = request.files.getlist('file_upload')
        downloaded_files = request.form.getlist('file_download')

        # Handle user login
        if len(username) != 0 and len(password) != 0:
            with open('users.json') as json_file:
                data = json.load(json_file)
            for user in data:
                salt_file = open("salt.txt", 'r')
                salt = salt_file.readlines()[0]
                salt_file.close()
                if username == user['username'] and hashlib.sha512((password + salt).encode('UTF-8')).hexdigest() == user['password']:
                    fNames = [x.name for x in os.scandir(app.config['UPLOAD_FOLDER'] + username + "/")]
                    session["username"] = username
                    return render_template('items.html', fNames=fNames, user=session['username'])
        if "username" not in session:
            return render_template('login.html')

        fNames = [x.name for x in os.scandir(app.config['UPLOAD_FOLDER'] + session['username'] + "/")]

        # Handles file uploads
        for f in uploaded_files:
            name = secure_filename(f.filename)
            if name != "":
                while name in fNames:  # Handles file duplicates
                    name = name[0:name.rfind('.')] + "-" + name[name.rfind('.'):len(name)]
                f.save(app.config['UPLOAD_FOLDER'] + session['username'] + "/" + name)

        # Handles file downloads
        if len(downloaded_files) > 1:  # If user tries to download more than one file
            with zipfile.ZipFile(session['username'] + '_' + 'data.zip', 'w') as f:
                for file in downloaded_files:
                    f.write(app.config['UPLOAD_FOLDER'] + session['username'] + "/" + file)
            return send_file(session['username'] + '_' + "data.zip", as_attachment=True)
        elif len(downloaded_files) == 1:  # If user tries to download exactly 1 file
            return send_file(app.config['UPLOAD_FOLDER'] + session['username'] + "/" + downloaded_files[0], as_attachment=True)

    # If user is not logged in
    if 'username' not in session:
        return render_template('login.html')
    # If user is logged in
    else:
        if os.path.exists(session['username'] + '_' + 'data.zip'):
            os.remove(session['username'] + '_' + 'data.zip')
        fNames = [x.name for x in os.scandir(app.config['UPLOAD_FOLDER'] + session['username'] + "/")]
        return render_template('items.html', fNames=fNames, user=session['username'])


if __name__ == '__main__':
    # print(socket.gethostbyname(socket.gethostname()))
    app.run(debug=True, host="0.0.0.0", port=25565, threaded=True)
