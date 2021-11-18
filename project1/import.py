import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Creates books table.

engine = create_engine("postgres://zrywcjzuzjxtzg:cce93106261d654e3c6da03a671762119be778b6fa7c65316b8bd0a926fcd5b8@ec2-54-243-212-227.compute-1.amazonaws.com:5432/d46dv6s8uol8j1", pool_pre_ping=True)
db = scoped_session(sessionmaker(bind=engine))

def main():
    db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year VARCHAR NOT NULL)")
    f = open("books.csv")
    reader = csv.reader(f)
    #next(reader, None)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book {isbn} : {title} : {author} : {year} to books.")
    db.commit()

if __name__ == "__main__":
    main()
