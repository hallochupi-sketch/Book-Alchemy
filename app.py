# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from data_models import db, Author, Book  # import from data_models.py

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = "dev"

db.init_app(app)

# create tables at startup once
with app.app_context():
    db.create_all()


@app.route("/")
def index():
    sort = request.args.get("sort", "title")
    search_term = request.args.get("q", "").strip()

    query = Book.query.join(Author)

    if search_term:
        like_pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Book.title.ilike(like_pattern),
                Author.first_name.ilike(like_pattern),
                Author.last_name.ilike(like_pattern),
            )
        )

    if sort == "title":
        query = query.order_by(Book.title)
    elif sort == "author":
        query = query.order_by(Author.last_name, Author.first_name, Book.title)

    books = query.all()

    return render_template("home.html", books=books, sort=sort)


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        author = Author(first_name=first_name, last_name=last_name)
        db.session.add(author)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    authors = Author.query.order_by(Author.last_name, Author.first_name).all()

    if request.method == "POST":
        title = request.form["title"]
        author_id = request.form["author_id"]

        book = Book(title=title, author_id=author_id)
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add_book.html", authors=authors)

@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author = book.author

    db.session.delete(book)
    db.session.flush()

    if author:
        # ensure the book is removed from the in-memory collection
        if book in author.books:
            author.books.remove(book)

        if len(author.books) == 0:
            db.session.delete(author)

    db.session.commit()
    flash("Book deleted successfully.")
    return redirect(url_for("index"))



if __name__ == "__main__":
    app.run(debug=True)
