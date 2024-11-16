from flask import Flask, render_template, request
import db_functions

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def index():
    owncall = db_functions.get_own_callsign()
    if request.method == 'POST':  # A search was used
        call = request.form.get('callsign').upper()
        if call == "":
            blog = db_functions.get_all_blog()
            return render_template("index.html", blog=blog, title="Main Feed", call=owncall)
        blog = db_functions.get_callsign_blog(call, 0)
        title = f"{call}'s Feed"
        if call == owncall:
            return render_template("qth.html", blog=blog, title=title, call=owncall)
        else:
            return render_template("index.html", blog=blog, title=title, call=owncall)
    else:  # Default Main Page
        blog = db_functions.get_all_blog()
        return render_template("index.html", blog=blog, title="Main Feed", call=owncall)


@app.route("/monitoring")
def monitoring():
    owncall = db_functions.get_own_callsign()
    blog = db_functions.get_monitoring_blog()
    return render_template("index.html", blog=blog, title="Monitoring Feed", call=owncall)


@app.route("/qth")
def qth():
    owncall = db_functions.get_own_callsign()
    blog = db_functions.get_callsign_blog(owncall, 0)
    title = f"{owncall} Feed"
    return render_template("qth.html", blog=blog, title=title, call=owncall)


@app.route("/callsign/<call>")
def callsign(call):
    owncall = db_functions.get_own_callsign()
    blog = db_functions.get_callsign_blog(call, 0)
    title = f"{call}'s Feed"
    return render_template("index.html", blog=blog, title=title, call=owncall)


###########################################
# Background processes without refreshing #
###########################################
@app.route('/addmon', methods=['POST'])
def addmon():
    db_functions.add_monitoring(request.form.get('addmon'))
    return "nothing"


@app.route('/delmon', methods=['POST'])
def delmon():
    db_functions.remove_monitoring(request.form.get('delmon'))
    return "nothing"


if __name__ == "__main__":
    app.run()