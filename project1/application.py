import os
import requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("signup.html")


@app.route("/guest", methods=["POST", "GET"])
def guest():

    session["user_name"] = "Guest"
    user_name = "Guest"

    # if request.method == "POST":
    #     try:
    #         user_name = session["user_name"]
    #     except NameError:
    #         user_name = ""
    # if request.method == "GET":
    #     try:
    #         user_name = session["user_name"]
    #     except NameError:
    #         user_name = ""

    return render_template("index.html", user_name=user_name)

@app.route("/home", methods=["POST", "GET"])
def real():

    if request.method == "POST":
        try:
            user_name = session["user_name"]
        except NameError:
            user_name = "Guest"
    if request.method == "GET":
        try:
            user_name = session["user_name"]
        except NameError:
            user_name = "Guest"

    return render_template("realindex.html", user_name=user_name)

@app.route("/home/allbooks")
def books():
    """Lists all books"""
    user_name = session["user_name"]
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("books.html", books=books, user_name=user_name)

reviews = []

@app.route("/home/book/<book_id>", methods=["GET", "POST"])
def book(book_id):


    name = request.form.get("name")
    review = request.form.get("review")
    rating = request.form.get("value")

# if user_name htbe ""

    if request.method == "POST":
        try:
            user_name = session["user_name"]
        except NameError:
            return render_template("signup.html")
        if db.execute("SELECT * FROM reviews WHERE book_id=:id AND reviewer=:user_name", {"id": book_id, "user_name": user_name}).rowcount == 1:
            return "You already made a review for this book."
        elif user_name == "Guest":
            return render_template("signup.html")
        else:
            review = request.form.get("review")
            rating = int(request.form.get("star"))
            db.execute("INSERT INTO reviews (review, reviewer, book_id, rating) VALUES (:review, :reviewer, :book_id, :rating)", {"review": review, "reviewer": user_name, "book_id": book_id, "rating": rating})
            db.commit()
    else:
        print('Please make an original review')



    """Collects all reviews about a single book."""
    # for ("SELECT rating FROM reviews WHERE id=:id", {"id": book_id}).fetchone() in rating:
    ratings=[]
    book_ratings=db.execute("SELECT rating FROM reviews WHERE book_id=:id", {"id": book_id}).fetchall()
    nn=0
    for n in book_ratings:
        nn+=1
        n=list(n)
        ratings.append(n[0])

    # book_ratings = tuple(book_rating)
    # book_ratings = list(book_rating)

    # return str(ratings)
    ii=0
    for i in ratings:
        ii+=1
        i = int(str(i))
        ratings[ii-1]=i

    if len(ratings) == 0:
        avg_book_rating = ' "Be the first to rate." '
    else:
        avg_book_rating = ("%.2f" % (sum(ratings)/len(ratings)))

    reviews = db.execute("SELECT * FROM reviews WHERE book_id= :id", {"id": book_id}).fetchall()
    user_name = session["user_name"]
    # return str(reviews)
    # if reviews is None:
    #     return render_template("error.html", message="No such book.")

#goodreads API
    book_isbn = db.execute("SELECT isbn FROM books WHERE id=:id", {"id": book_id}).fetchall()

    API_KEY = "7ybyomwIQ0QTeCejzuSt0A"

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7ybyomwIQ0QTeCejzuSt0A", "isbns": book_isbn})
    if res.status_code != 200:
        raise Exception("API Error")
    data = res.json()
    info = data["books"][0]
    ratings_count = info["ratings_count"]
    average_rating = info["average_rating"]

    """Lists details about a single book."""
    book = db.execute("SELECT * FROM books WHERE id= :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    return render_template("book.html", book=book, review=review, reviews=reviews, rating=rating, avg_book_rating=avg_book_rating, user_name=user_name, average_rating=average_rating, ratings_count=ratings_count)

@app.route("/home/find", methods=["POST", "GET"])
def find():
    """Finds Book Details from ID"""
    # name = request.form.get("name")
    # try:
    #     book_id = (request.form.get("book_id"))
    # except ValueError:
    #     return render_template("error.html", message="Invalid Book Number")
    book_id = int((request.args.get("book_id")))

    if db.execute("SELECT * FROM books WHERE id= :id", {"id": book_id}).rowcount == 0:
        return render_template("results.html", message="No Results Found")

    return book(book_id)

@app.route("/search/query", methods=["POST", "GET"])
def query():
    user_name = session["user_name"]

    """Finds Book Details from QUERY"""
    name = request.form.get("name")
    try:
        book_query = (request.form.get("book_id"))
    except ValueError:
        return render_template("error.html", message="Invalid Query")

    book = db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (UPPER(title) LIKE UPPER(:query)) OR (UPPER(author) LIKE UPPER(:query))", {"query": book_query}).fetchone()
    if int(str(db.execute("SELECT * FROM books WHERE author= :query", {"query": book_query}).rowcount)) > 0 :
        books = db.execute("SELECT * FROM books WHERE author= :query", {"query": book_query}).fetchall()
        return render_template("results.html", books=books, book=book, message="Search Results", user_name=user_name)
    elif int(str(db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (UPPER(title) LIKE UPPER(:query)) OR (UPPER(author) LIKE UPPER(:query))", {"query": '%' + book_query + '%'}).rowcount)) > 1 :
        books = db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (UPPER(title) LIKE UPPER(:query)) OR (UPPER(author) LIKE UPPER(:query))", {"query": '%' + book_query + '%'}).fetchall()
        return render_template("results.html", books=books, book=book, message="Search Results", user_name=user_name)
    elif int(str(db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (UPPER(title) LIKE UPPER(:query)) OR (UPPER(author) LIKE UPPER(:query))", {"query": '%' + book_query + '%'}).rowcount)) == 0 :
        return render_template("results.html", message="No results found")
    # elif book_query not in db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (title LIKE :query) OR (author LIKE :query)", {"query": '%' + book_query + '%'}).fetchall():
    #     return render_template("error.html", message="Nothing found.")
    else:
        books = db.execute("SELECT * FROM books WHERE (isbn LIKE :query) OR (UPPER(title) LIKE UPPER(:query)) OR (UPPER(author) LIKE UPPER(:query))", {"query": '%' + book_query + '%'}).fetchall()
        return render_template("results.html", books=books, book=book, message="Search Results", user_name=user_name)
    if book is None:
        return render_template("error.html", message="No such book isbn.")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/registration", methods=["POST"])
def register():
    name = request.form.get("name")
    try:
        user_email = (request.form.get("email"))
        user_name = (request.form.get("username"))
        user_paz = (request.form.get("paz"))
    except ValueError:
        return render_template("error.html", message="Unable to process request at this time.")

    if db.execute("SELECT * FROM users WHERE email = :email", {"email": user_email}).rowcount >= 1:
        return render_template("error.html", message="email already registered")
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": user_name}).rowcount >= 1:
        return render_template("error.html", message="username unavailable")
    else:
        db.execute("INSERT INTO users (email, username, paz) VALUES (:email, :username, :paz)", {"email": user_email, "username": user_name, "paz": user_paz})
        db.commit()
        return render_template("sucess.html")

@app.route("/home/signin", methods=["POST"])
def signin():
    name = request.form.get("name")
    session["user_name"] = request.form.get("username")
    p = session["user_name"]
    try:
        user_name = request.form.get("username")
        user_paz = (request.form.get("paz"))
    except ValueError:
        return render_template("error.html", message="Something went wrong.")

    user_name = db.execute("SELECT username FROM users WHERE username= :username AND paz= :paz", {"username": user_name, "paz": user_paz}).fetchone()
    if user_name is None:
        return render_template("error.html", message="Username or Password are invalid.")
    else:
        for name in user_name:
            user_name = name

    return render_template("realindex.html", user_name=user_name)

@app.route("/ReadandRate/home/signedin", methods=["GET"])
def signedin():
    try:
        user_name = session["user_name"]
    except NameError:
        user_name = "Guest"

    return real()

@app.route("/home/about")
def about():
    user_name = session["user_name"]
    return render_template("about.html", user_name=user_name)

@app.route("/home/contact")
def contact():
    user_name = session["user_name"]
    return render_template("contact.html", user_name=user_name)

@app.route("/random")
def random():
    return render_template("random.html")

@app.route("/api/books/<book_isbn>")
def book_api(book_isbn):

    if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).rowcount < 1:
        print(book_isbn)
        # return jsonify({"error": "Invalid book_isbn"}), 404

    book = db.execute("SELECT * FROM books WHERE isbn= :isbn", {"isbn": book_isbn}).fetchone()
    book_id = db.execute("SELECT id FROM books WHERE isbn= :isbn", {"isbn": book_isbn}).fetchall()
    book_id = list(book_id[0])
    book_id = book_id[0]
    book_ratings =db.execute("SELECT rating FROM reviews WHERE book_id=:id", {"id": book_id}).fetchall()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id= :id", {"id": book_id}).rowcount

    ratings=[]
    book_ratings=db.execute("SELECT rating FROM reviews WHERE book_id=:id", {"id": book_id}).fetchall()
    nn=0
    for n in book_ratings:
        nn+=1
        n=list(n)
        ratings.append(n[0])

    # return str(ratings)
    ii=0
    for i in ratings:
        ii+=1
        i = int(str(i))
        ratings[ii-1]=i

    if len(ratings) == 0:
        avg_book_rating = ' "Be the first to rate." '
    else:
        avg_book_rating = ("%.2f" % (sum(ratings)/len(ratings)))

    return jsonify({
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": book.isbn,
    "review_count": reviews ,
    "average_score": avg_book_rating,
    })


@app.route("/AGT")
def AGT():
    book_id = '666'
    return book(book_id)

@app.route("/IT")
def IT():
    book_id = '67'
    return book(book_id)

@app.route("/HMT")
def HMT():
    book_id = '1050'
    return book(book_id)
