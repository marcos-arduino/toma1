from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/peliculas/<int:id>", methods=["GET"])
def cargar_pelicula(id):
	conn = get_db_connection()
	pelicula = conn.execute("SELECT * FROM peliculas WHERE id = ?", (id,)).fetchone()
	conn.commit()
	conn.close()
	return render_template("pelicula.html", pelicula=pelicula)
    

if __name__ == "__main__":
    app.run(debug=True)