from flask import Response, render_template_string, send_file
from camera_stream import gen_frames
from flask_utils import plot_histogram, reset_histogram, close_app
import os

RESPATH= 'results'
STATPATH= 'static'



def configure_routes(app):

    @app.route('/')
    def index():
        return render_template_string("""<!DOCTYPE html>
    <html>
    <head>
        <title>Dice Detection System</title>
        <link rel="icon" href="{{ url_for('static', filename='logo.ico') }}" type="image/x-icon">
        <style>
            @font-face {
                font-family: 'Helvetica Rounded Bold';
                src: url('helvetica-rounded-bold.woff2') format('woff2'),
                    url('helvetica-rounded-bold.woff') format('woff');
                font-weight: bold;
                font-style: normal;
            }

            body {
                font-family: 'Helvetica Rounded Bold', Arial, sans-serif;
                background-color: white;
                color: #333;
                margin: 0;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }

            .header, .footer {
                background-color: #0165A8;
                color: white;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 1000;
            }

            .header {
                min-height: 70px;
            }

            .footer {
                display: flex;
                align-items: center;
                justify-content: space-between;
                text-align: right;
            }

            .footer img {
                max-height: 100px;
                margin: 5px 10px;
            }

            .content {
                display: flex;
                flex-direction: row;
                justify-content: space-around;
                margin: 10px; /* Margin around content */
                flex-grow: 1;
                overflow: auto;
            }

            .box {
                display: flex;
                justify-content: center;
                flex-direction: column;
                align-items: center;
                border: 2px solid #0073e6;
                margin: 10px; /* Margin around each box */
                text-align: center;
                flex-grow: 1;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Dice Detection System</h1>
        </div>

        <div class="content">
            <div class="box">
                <h2>Camera Stream</h2>
                <img src="/video_feed" alt="Camera Stream">
            </div>
            
            <div class="box">
                <h2>Histogram</h2>
                <img id="histogram" src="/plot.png" alt="Histogram">
                <button onclick="resetHistogram()">Reset Histogram</button>
            </div>
        </div>

        <div class="footer">
            <img src="{{ url_for('static', filename='ZHAW_IDP_white.png') }}" alt="IDP-Logo">
        </div>

        <script>
            function refreshImage() {
                var img = document.getElementById("histogram");
                var newSrc = "/plot.png?random=" + Math.random();
                img.src = newSrc;
            }
            setInterval(refreshImage, 1000); // Refresh every 1000 milliseconds

            function resetHistogram() {
                fetch('/reset_histogram', { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        console.log("Histogram reset successfully.");
                        refreshImage(); // Refresh the histogram image
                    }
                })
                .catch(error => console.error('Error:', error));
            }

            window.onbeforeunload = function() {
                navigator.sendBeacon('/close_app');
            }
        </script>
    </body>
    </html>
    """)

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/plot.png')
    def plot_png():
        data_path = os.path.join(RESPATH, 'res.csv')  # Replace with your CSV file path
        column_name = 'Numbers'         # Replace with the column name
        img = plot_histogram(data_path, column_name)
        return send_file(img, mimetype='image/png')


    @app.route('/reset_histogram', methods=['POST'])
    def reset_histogram_route():
        return reset_histogram()

    @app.route('/close_app', methods=['POST'])
    def close_app_route():
        return close_app()
