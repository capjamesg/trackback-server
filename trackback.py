import indieweb_utils
import psycopg2
from flask import Flask, jsonify, render_template, request

from config import DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER

app = Flask(__name__)

database = psycopg2.connect(
    "dbname={} user={} password={}".format(
        DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
    )
)


def paginate(collection, page, per_page):
    # create list of lists
    pages = [collection[i : i + per_page] for i in range(0, len(collection), per_page)]

    # return requested page
    return pages[page - 1]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/trackback", methods=["GET", "POST"])
def trackback():
    if request.method == "GET":
        page = int(request.args.get("page", 1))
        url = request.args.get("url", None)

        if not url:
            return jsonify({"success": False, "error": "url parameter required."}), 400

        cursor = database.cursor()
        cursor.execute("SELECT * FROM trackbacks WHERE url = %s", (url,))
        trackbacks = cursor.fetchall()

        trackbacks = paginate(trackbacks, page, 10)

        cursor.close()

        return jsonify({"success": True, "trackbacks": trackbacks}), 200

    post_url = request.form.get("url")
    request_content_type = request.headers.get("Content-Type")

    response = indieweb_utils.process_trackback(post_url, request_content_type)

    if "error" not in response:
        cursor = database.cursor()

        excerpt = request.form.get("excerpt", "")
        blog_name = request.form.get("blog_name", "")
        title = request.form.get("title", "")

        cursor.execute(
            "INSERT INTO trackbacks (url, excerpt, blog_name, title) VALUES (%s, %s, %s, %s)",
            (post_url, excerpt, blog_name, title),
        )
        database.commit()
        cursor.close()

    return response

@app.route("/send", methods=["POST"])
def send():
    source_url = request.form.get("source")
    target_url = request.form.get("target")
    title = request.form.get("title", "")
    excerpt = request.form.get("excerpt", "")
    blog_name = request.form.get("blog_name", "")

    try:
        response = indieweb_utils.send_trackback(target_url, source_url, title, excerpt, blog_name)
    except Exception as e:
        return jsonify({"success": False, "error": "bad request"}), 400

    return jsonify({"success": True}), 200

if __name__ == "__main__":
    app.run()
