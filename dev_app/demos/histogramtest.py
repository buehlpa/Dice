from flask import Flask, send_file, render_template_string
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib
matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()
app = Flask(__name__)

def plot_histogram(data_path, column_name):
    with matplotlib_lock:
        df = pd.read_csv(data_path)
        print(df)
        plt.figure()
        df[column_name].hist()
        
        
        plt.title(f'Histogram of {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img

@app.route('/plot.png')
def plot_png():
    data_path = r'C:\Users\buehl\repos\Dice\rasperry_run\results\res.csv'  # Replace with your CSV file path
    column_name = 'Numbers'         # Replace with the column name
    img = plot_histogram(data_path, column_name)
    return send_file(img, mimetype='image/png')

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Histogram Display</title>
        <script>
            function refreshImage() {
                var img = document.getElementById("histogram");
                var newSrc = "/plot.png?random=" + Math.random();
                img.src = newSrc;
            }
            setInterval(refreshImage, 1000); // Refresh every 1000 milliseconds (1 second)
        </script>
    </head>
    <body>
        <h1>Histogram Updated Every Second</h1>
        <img id="histogram" src="/plot.png" alt="Histogram">
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
