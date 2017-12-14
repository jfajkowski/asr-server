from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/upload')
def load_page():
    return render_template('upload.html')


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        file.save(file.filename)
        return 'file uploaded successfully'


if __name__ == '__main__':
    app.run(debug=True)