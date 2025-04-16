from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify , Response
from flask_cors import CORS
import datetime
import sqlite3
import secrets
import jwt
import uuid
from flask_mail import Mail
from flask_mail import Message
import redis
'''from celerytask import send_email , download_csv 
from tasks import send_daily_emails'''
import time

app = Flask("EventVisa")



CORS(app)


app.config['SECRET_KEY'] = "73372646473cc92a1e5e19401343acf41913face76a39ae703634fc13545b6c5273f6354815c0e245cd8253cb4b5fd116dcf426ed1f7babd4eb8227ae3130"

connection = sqlite3.connect('eventvisa.db')



connection.execute(
    "CREATE TABLE IF NOT EXISTS admin ( Name	TEXT NOT NULL, UserID	TEXT NOT NULL UNIQUE PRIMARY KEY, Password	TEXT NOT NULL);"
)

connection.execute(
    "CREATE TABLE IF NOT EXISTS user (Phone	INTEGER NOT NULL UNIQUE ,Email	TEXT NOT NULL UNIQUE PRIMARY KEY, Name	TEXT NOT NULL, DoB	TEXT NOT NULL,Address	TEXT, Address2	TEXT, City	TEXT, State	TEXT,PinCode	INTEGER,Password	TEXT NOT NULL);"
)

connection.execute('''
        CREATE TABLE IF NOT EXISTS theater (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            available_vip_seats INTEGER,
            available_elite_seats INTEGER,
            available_general_seats INTEGER,
            UNIQUE (name, address)
        )
    ''')

connection.execute('''CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rating TEXT NOT NULL CHECK (rating IN ('U', 'UA', 'A', 'S'))
)''')

connection.execute('''CREATE TABLE IF NOT EXISTS shows (
    show_id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    theater_id INTEGER NOT NULL,
    show_time DATETIME NOT NULL,
    available_vip_tickets INTEGER NOT NULL CHECK (available_vip_tickets >= 0),
    available_elite_tickets INTEGER NOT NULL CHECK (available_elite_tickets >= 0),
    available_general_tickets INTEGER NOT NULL CHECK (available_general_tickets >= 0),
    price_per_vip_ticket REAL NOT NULL,
    price_per_elite_ticket REAL NOT NULL,
    price_per_general_ticket REAL NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id),
    FOREIGN KEY (theater_id) REFERENCES theaters (theater_id)
)''')

connection.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY ,
        theater_name TEXT,
        movie_name TEXT,
        show_time TEXT,
        user_email TEXT,
        vip_seats INTEGER,
        elite_seats INTEGER,
        general_seats INTEGER,
        total_price REAL,
        date TEXT
    )
''')

connection.commit()

try:

  insert_query = ("INSERT INTO admin  (Name , UserID , Password)"
                  "VALUES (:name, :user, :pass);")

  parameters = {'name': 'Admin Swastik', 'user': 'admin', 'pass': 'Admin@123'}

  connection.execute(insert_query, parameters)
  connection.commit()
  connection.close()
except sqlite3.IntegrityError:
  connection.close()
  pass


#send_daily_emails.delay()

def generate_token(name, role, dob, address, phone, email):

  payload = {
      'name':
      name,
      'exp':
      datetime.datetime.now(datetime.timezone.utc) +
      datetime.timedelta(hours=1),  # Token will expire in 1 hour
      'role':
      role,
      'dob':
      dob,
      'address':
      address,
      'phone':
      phone,
      'email':
      email
  }
  token = jwt.encode(
      payload, app.config['SECRET_KEY'],
      algorithm='HS256')  # Use jwt.encode() from the pyjwt library

  return token


   

@app.route("/get_user_name", methods=['POST'])
def get_user_name():

  token = request.get_json().get('token')

  try:
    payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    user_name = payload.get('name')
    role = payload.get('role')
    dob = payload.get('dob')
    address = payload.get('address')
    phone = payload.get('phone')
    email = payload.get('email')
    return jsonify({
        'success': True,
        'user_name': user_name,
        'role': role,
        'dob': dob,
        'address': address,
        'phone': phone,
        'email': email
    })
  except jwt.ExpiredSignatureError:
    return jsonify({'success': False, 'message': 'Session Expired'})
  except jwt.InvalidTokenError:
    return jsonify({'success': False, 'message': 'Unauthorised'})


@app.route("/get_role", methods=['POST'])
def get_role():
  token = request.get_json().get('token')
  try:
    payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    role = payload.get('role')
    email=payload.get('email')
    return jsonify({
        'success': True,
        'role': role,
        'email':email
    })  # Return the dictionary directly, no need for jsonify here
  except jwt.ExpiredSignatureError:
    return jsonify({
        'success': False,
        'error': "Please Login Again"
    })  # Token has expired
  except jwt.InvalidTokenError:
    return jsonify({
        'success': False,
        'error': "Access Denied"
    })  # Invalid token
  return jsonify({'success': False, 'error': "Unknown Error"})


@app.route("/home.html")
def home():
  return render_template("home.html")


@app.route("/movies.html")
def movies():
  return render_template("movies.html")


@app.route("/")
def hello_world():
  return render_template("home.html")


@app.route("/signup.html", methods=['GET', 'POST'])
def signup():
  if request.method == 'POST':
    # Get the form data from the request
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    dob = data.get('dob')
    address1 = data.get('address1')
    address2 = data.get('address2')
    city = data.get('city')
    state = data.get('state')
    pin = data.get('pin')
    phone = data.get('phone')

    address = address1 + " , " + address2 + " , " + city + " , " + state + " - " + pin

    # Check if the email already exists in the database
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM user WHERE Email = ?", (email, ))
    count_email = cursor.fetchone()[0]
    print(type(count_email), count_email)
    if count_email > 0:

      return jsonify({'success': False, 'message': 'Email already exists.'})

    cursor.execute("SELECT COUNT(*) FROM user WHERE Phone = ?", (phone, ))
    count_phone = cursor.fetchone()[0]
    if count_phone > 0:
      return jsonify({'success': False, 'message': 'Phone already exists.'})

    else:

      insert_query = (
          "INSERT INTO user(Phone, Email, Name, DoB, Address, Address2, City, State, PinCode, Password)"
          "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);")
      parameters = (phone, email, name, dob, address1, address2, city, state,
                    pin, password)

      cursor.execute(insert_query, parameters)
      conn.commit()
      conn.close()
      token = generate_token(name, "client", dob, address, phone, email)
      welcome="Hey! "+name+" Welcome To EventVisa! Now Never Miss On Exciting Offers And Deals!"
      send_email("help.eventvisa@gmail.com",email,"Namaskar-EventVisa",welcome)
      return jsonify({
          'success': True,
          'message': 'User registered successfully.',
          'token': token
      })

  else:
    return render_template("signup.html")


@app.route("/signin.html", methods=['GET', 'POST'])
def signin():
  if request.method == 'POST':

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Check the email and password in the database
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM User WHERE Email = ? AND Password = ?",
        (email, password))
    count = cursor.fetchone()[0]
    if count == 1:
      cursor.execute("SELECT Name From User Where Email = ?", (email, ))
      name = cursor.fetchone()[0]
      cursor.execute("SELECT dob From User Where Email = ?", (email, ))
      dob = cursor.fetchone()[0]
      cursor.execute("SELECT address From User Where Email = ?", (email, ))
      address1 = cursor.fetchone()[0]
      cursor.execute("SELECT address2 From User Where Email = ?", (email, ))
      address2 = cursor.fetchone()[0]
      cursor.execute("SELECT city From User Where Email = ?", (email, ))
      city = cursor.fetchone()[0]
      cursor.execute("SELECT state From User Where Email = ?", (email, ))
      state = cursor.fetchone()[0]
      cursor.execute("SELECT PinCode From User Where Email = ?", (email, ))
      pin = str(cursor.fetchone()[0])
      cursor.execute("SELECT phone From User Where Email = ?", (email, ))
      phone = cursor.fetchone()[0]

      address = address1 + " , " + address2 + " , " + city + " , " + state + " - " + pin
      token = generate_token(name, "client", dob, address, phone, email)
      conn.close()
      return jsonify({
            'success': True,
            'message': 'Authentication successful.',
            'token': token
        })
    else:
      # Unsuccessful authentication, return an error message
      conn.close()
      return jsonify({
          'success': False,
          'message': 'Invalid email or password.'
      })
  else:
    return render_template("signin.html")


@app.route("/admin_login.html", methods=['GET', 'POST'])
def admin_login():
  if request.method == 'POST':

    data = request.get_json()
    user = data.get('user')
    password = data.get('password')

    # Check the email and password in the database
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM admin WHERE UserID = ? AND Password = ?",
        (user, password))
    count = cursor.fetchone()[0]
    cursor.execute("SELECT Name FROM admin WHERE UserID = ?", (user, ))
    name = cursor.fetchone()[0]

    if count == 1:
      # Successful authentication, generate token and return it in the response

      token = generate_token(name, "admin", "", "", "", "")
      conn.close()
      return jsonify({
          'success': True,
          'message': 'Authentication successful.',
          'token': token
      })
    else:
      # Unsuccessful authentication, return an error message
      conn.close()
      return jsonify({'success': False, 'message': 'Access Denied'})
  else:
    return render_template("admin_signin.html")


@app.route("/admin_landing.html")
def admin_landing():
    return render_template("admin_landing.html")

@app.route("/theater_csv",methods=['POST'])
def theather_csv():
    if request.method=='POST':
      theater_id = request.form['theater_id']
      conn = sqlite3.connect('eventvisa.db')
      cursor = conn.cursor()
      print("id: "+theater_id)
      theater_data = cursor.execute('SELECT * FROM theater WHERE id = ?', (theater_id,)).fetchone()
      print(theater_data)
      conn.close()
      return(download_csv(theater_data))


@app.route("/movies_admin.html")
def movie_admin():
  return render_template("movies_admin.html")

@app.route("/generate_booking_report", methods=['POST'])
def generate_booking_report():
    try:
        conn = sqlite3.connect("eventvisa.db")
        cursor = conn.cursor()

        # Fetch all bookings from the database
        cursor.execute("SELECT * FROM bookings")
        all_bookings = cursor.fetchall()

        conn.close()

        # Render the HTML template using all_bookings data
        html = render_template("all_bookings_template.html", all_bookings=all_bookings)

        # Create a Response with HTML content and appropriate headers
        response = Response(html, content_type="text/html")
        response.headers["Content-Disposition"] = "attachment; filename=all_bookings.html"
       
        return response

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
      
@app.route("/add_theater", methods=["POST"])
def add_theater():
  data = request.json

  try:
    # Connect to the database
    conn = sqlite3.connect("eventvisa.db")
    cursor = conn.cursor()

    # Check if theater with the same name and address exists (case-insensitive and trimmed)
    cursor.execute(
        '''
            SELECT COUNT(*) FROM theater WHERE LOWER(name) = ? AND LOWER(address) = ?
        ''', (data['name'].strip().lower(), data['address'].strip().lower()))

    count = cursor.fetchone()[0]

    if count > 0:
      conn.close()
      return jsonify({
          'success':
          False,
          'message':
          'Theater with the same name and address already exists'
      })

    # Insert the theater data into the table, excluding the ID
    cursor.execute(
        '''
            INSERT INTO theater (name, address, available_vip_seats, available_elite_seats, available_general_seats)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'].strip(), data['address'].strip(),
              data['availableVIPSeats'], data['availableEliteSeats'],
              data['availableGeneralSeats']))

    # Commit the changes
    conn.commit()

    # Get the last inserted ID (auto-generated) and send it in the response
    theater_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Theater added successfully',
        'theater_id': theater_id,
        'name': data['name']
    })
  except Exception as e:
    return jsonify({'success': False, 'error': str(e)})


@app.route("/add_movie", methods=["POST"])
def add_movie():
  data = request.json
  name = data.get("name")
  rating = data.get("rating")

  if not name or not rating:
    return jsonify({
        "success": False,
        "message": "Please provide name and rating."
    })

  try:
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    # Check if the movie with the same name already exists
    cursor.execute("SELECT COUNT(*) FROM movies WHERE name = ?", (name, ))
    count = cursor.fetchone()[0]

    if count > 0:
      conn.close()
      return jsonify({
          "success": False,
          "message": "Movie with the same name already exists."
      })

    # Insert the new movie into the database
    cursor.execute("INSERT INTO movies (name, rating) VALUES (?, ?)",
                   (name, rating))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Movie added successfully."})

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


# Route to add a new show
@app.route("/add_show", methods=["POST"])
def add_show():
  data = request.json
  movie_id = data.get("movie_id")
  theater_id = data.get("theater_id")
  show_time = data.get("show_time")
  available_vip_tickets = data.get("available_vip_tickets")
  available_elite_tickets = data.get("available_elite_tickets")
  available_general_tickets = data.get("available_general_tickets")
  price_per_vip_ticket = data.get("price_per_vip_ticket")
  price_per_elite_ticket = data.get("price_per_elite_ticket")
  price_per_general_ticket = data.get("price_per_general_ticket")

  if not all([
      movie_id, theater_id, show_time, available_vip_tickets,
      available_elite_tickets, available_general_tickets, price_per_vip_ticket,
      price_per_elite_ticket, price_per_general_ticket
  ]):
    return jsonify({
        "success": False,
        "message": "Please provide all required fields."
    })

  try:
    conn = sqlite3.connect('eventvisa.db')
    cursor = conn.cursor()

    # Check if the show time clashes with existing shows for the same movie and theater
    cursor.execute(
        "SELECT COUNT(*) FROM shows WHERE movie_id = ? AND theater_id = ? AND show_time = ?",
        (movie_id, theater_id, show_time))
    count = cursor.fetchone()[0]

    if count > 0:
      conn.close()
      return jsonify({
          "success":
          False,
          "message":
          "Show time clashes with an existing show for the same movie and theater."
      })

    # Insert the new show into the database
    cursor.execute(
        "INSERT INTO shows (movie_id, theater_id, show_time, available_vip_tickets, available_elite_tickets, available_general_tickets, price_per_vip_ticket, price_per_elite_ticket, price_per_general_ticket) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (movie_id, theater_id, show_time, available_vip_tickets,
         available_elite_tickets, available_general_tickets,
         price_per_vip_ticket, price_per_elite_ticket,
         price_per_general_ticket))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Show added successfully."})

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route("/get_movies", methods=["POST"])
def get_movies():
  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all movies from the database
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    conn.close()

    # Convert movie data to a list of dictionaries
    movies_list = []
    for movie in movies:
      movies_list.append(dict(movie))

    return jsonify({"success": True, "movies": movies_list})

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


# Route to fetch available theaters


@app.route("/get_theaters", methods=["POST"])
def get_theaters():
  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all theaters from the database
    cursor.execute("SELECT * FROM theater")
    theaters = cursor.fetchall()
    conn.close()

    print(theaters)

    # Convert theater data to a list of dictionaries
    theaters_list = []

    for theater in theaters:
      theaters_list.append(dict(theater))

    return jsonify({"success": True, "theaters": theaters_list})

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})




@app.route("/update_movie", methods=["POST"])
def update_movie():
  data = request.json

  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')

    cursor = conn.cursor()

    # Check if the movie with the given ID exists
    cursor.execute("SELECT * FROM movies WHERE movie_id = ?",
                   (data["movie_id"], ))
    movie = cursor.fetchone()

    if not movie:
      conn.close()
      return jsonify({
          "success": False,
          "message": "Movie with the given ID does not exist"
      })

    # Update the movie details in the database
    cursor.execute("UPDATE movies SET name = ?, rating = ? WHERE movie_id = ?",
                   (data["name"], data["rating"], data["movie_id"]))

    # Commit the changes
    conn.commit()
    conn.close()

    return jsonify({  
        "success": True,
        "message": "Movie details updated successfully"
    })
  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


# Delete movie
@app.route("/delete_movie/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')

    cursor = conn.cursor()

    # Check if the movie with the given ID exists
    cursor.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id, ))
    movie = cursor.fetchone()

    if not movie:
      conn.close()
      return jsonify({
          "success": False,
          "message": "Movie with the given ID does not exist"
      })

    # Delete the movie from the database
    cursor.execute("DELETE FROM movies WHERE movie_id = ?", (movie_id, ))

    # Commit the changes
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Movie deleted successfully"})
  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route("/update_theater/<int:theater_id>", methods=["PUT"])
def update_theater(theater_id):
  data = request.json

  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')

    cursor = conn.cursor()

    # Check if the theater with the given ID exists
    cursor.execute("SELECT * FROM theater  WHERE id = ?",
                   (theater_id, ))
    theater = cursor.fetchone()

    if not theater:
      conn.close()
      return jsonify({
          "success": False,
          "message": "Theater with the given ID does not exist"
      })

    # Update the theater details in the database
    cursor.execute(
        "UPDATE theater  SET name = ?, address = ?, available_vip_seats = ?, available_elite_seats = ?, available_general_seats = ? WHERE id = ?",
        (data["name"], data["address"], data["availableVIPSeats"],
         data["availableEliteSeats"], data["availableGeneralSeats"],
         theater_id))

    # Commit the changes
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Theater details updated successfully"
    })
  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route("/delete_theater/<int:theater_id>", methods=["DELETE"])
def delete_theater(theater_id):
  try:
    # Connect to the database
    conn = sqlite3.connect('eventvisa.db')

    cursor = conn.cursor()

    # Check if the theater with the given ID exists
    cursor.execute("SELECT * FROM theater  WHERE id = ?",
                   (theater_id, ))
    theater = cursor.fetchone()

    if not theater:
      conn.close()
      return jsonify({"success": False, "message": "Theater Does Not Exsists"})

    cursor.execute("DELETE FROM theater  WHERE id = ?", (theater_id, ))

    # Commit the changes
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Theater deleted successfully"
    })
  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route("/get_theaters_with_movies_and_shows", methods=["POST"])
def get_theaters_with_movies_and_shows():
  try:
    # Fetch all theaters from the database
    conn = sqlite3.connect("eventvisa.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM theater")
    theaters = cursor.fetchall()

    # Create a list to store theaters with movies and shows
    theaters_with_movies_and_shows = []

    # Loop through each theater to fetch movies and shows
    for theater in theaters:
      theater_dict = {
          "theater_id": theater[0],
          "name": theater[1],
          "address": theater[2],
          "movies": []
      }

      # Fetch shows for the current theater
      cursor.execute(
          "SELECT show_id, movie_id, show_time, available_vip_tickets, available_elite_tickets, available_general_tickets, price_per_vip_ticket, price_per_elite_ticket, price_per_general_ticket FROM shows WHERE theater_id = ?",
          (theater[0], ))
      shows = cursor.fetchall()

      # Loop through each show and fetch the associated movie details
      for show in shows:
        cursor.execute("SELECT name FROM movies WHERE movie_id = ?",
                       (show[1], ))
        movie_name = cursor.fetchone()
        cursor.execute("SELECT rating FROM movies WHERE movie_id = ?",
                       (show[1], ))
        rating = cursor.fetchone()

        if movie_name:  # Check if movie_name is not None
          movie_name = movie_name[0]
        if rating:  # Check if movie_name is not None
          rating = rating[0]

          show_dict = {
              "show_id": show[0],
              "movie_id": show[1],
              "movie_name": movie_name,
              "rating": rating,
              "show_time": show[2],
              "available_vip_tickets": show[3],
              "available_elite_tickets": show[4],
              "available_general_tickets": show[5],
              "price_per_vip_ticket": show[6],
              "price_per_elite_ticket": show[7],
              "price_per_general_ticket": show[8]
          }

          theater_dict["movies"].append(show_dict)

      theaters_with_movies_and_shows.append(theater_dict)

    conn.close()

    return jsonify({
        "success": True,
        "theaters": theaters_with_movies_and_shows
    })

  except Exception as e:
    return jsonify({"success": False, "error": str(e)})


@app.route("/user_dashboard.html")
def user_dashboard():
  return render_template("user_dashboard.html")


@app.route("/book_ticket", methods=["POST"])
def book_ticket():
  try:
    data = request.json

    # Extract data from the request
    show_id = data.get("showId")
    vip_seats = int(data.get("vipSeats"))
    elite_seats = int(data.get("eliteSeats"))
    general_seats = int(data.get("generalSeats"))
    email=data.get("email")
    print(email)
    # Check if any seats are selected
    if vip_seats == 0 and elite_seats == 0 and general_seats == 0:
      print("Inside first if")
      return jsonify({
          "success": False,
          "message": "Select at least one type of seat."
      })

    conn = sqlite3.connect("eventvisa.db")
    cursor = conn.cursor()

    # Fetch show details
    cursor.execute("SELECT * FROM shows WHERE show_id = ?", (show_id, ))
    show = cursor.fetchone()
    print (vip_seats,show[4] , type(show[4]))
    print (elite_seats,show[5] , type(show[5]))
    print (general_seats,show[6] , type(show[6]))
    if not show:
      conn.close()
      return jsonify({"success": False, "message": "Show not found."})

    # Calculate total ticket price
    total_price = (vip_seats * show[7])+(elite_seats * show[8]) + (general_seats * show[9])
    print(total_price)
    # Check if there are enough available seats
    if vip_seats > show[4] or elite_seats > show[5] or general_seats > show[6]:
      conn.close()
      return jsonify({
          "success": False,
          "message": "Not enough available seats."
      })

    # Generate booking ID using UUID
    
    # Generate booking ID using UUID
    booking_id = str(uuid.uuid4())

    # Update available seats in the shows table
    new_vip_seats = show[4] - vip_seats
    new_elite_seats = show[5] - elite_seats
    new_general_seats = show[6] - general_seats
    
    # Fetch theater name from theater table
    cursor.execute("SELECT name FROM theater WHERE id = ?", (show[2],))
    theater_name = cursor.fetchone()[0]
    print(theater_name)
    # Fetch movie name from movies table
    cursor.execute("SELECT name FROM movies WHERE movie_id = ?", (show[1],))
    movie_name = cursor.fetchone()[0]
    print(movie_name)
    # Update available seats and commit
    try:
      cursor.execute(
        "UPDATE shows SET available_vip_tickets = ?, available_elite_tickets = ?, available_general_tickets = ? WHERE show_id = ?",
        (new_vip_seats, new_elite_seats, new_general_seats, show_id, ))
      conn.commit()
    except:
      print("Error is here in update")
    date=datetime.datetime.now(datetime.timezone.utc)  
    print(date)
    # Insert booking details into bookings table
    try:
      
      cursor.execute( "INSERT INTO bookings (id, theater_name, movie_name, show_time, user_email, vip_seats, elite_seats, general_seats, total_price, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      (booking_id, theater_name, movie_name, show[3], email, vip_seats, elite_seats, general_seats, total_price, date))

      conn.commit()
      
      conn.close()
      print("Done Till Here")
      return jsonify({
        "success": True,
        "message": "Booking successful!",
        "bookingId": booking_id,
        "totalPrice": total_price
      })
    except Exception as e:
      print(e)
      return jsonify({"success": False, "message": str(e)})

  
  except Exception as e:
    return jsonify({
      "success": False,
      "message": str(e)
    })





@app.route("/get_user_bookings", methods=["POST"])
def get_user_bookings():
    try:
        data = request.json
        user_email = data.get("email")
        print("Email: " , user_email)
        conn = sqlite3.connect("eventvisa.db")
        cursor = conn.cursor()

        # Fetch user-specific bookings
        cursor.execute("SELECT * FROM bookings WHERE user_email = ?", (user_email,))
        user_bookings = cursor.fetchall()

        conn.close()

        return jsonify({
            "success": True,
            "userBookings": user_bookings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

app.run(host="0.0.0.0", port=8080, debug=True)

print("Server is running on port 8080")