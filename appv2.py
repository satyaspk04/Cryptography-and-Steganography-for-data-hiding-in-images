from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify,after_this_request
import os
from werkzeug.utils import secure_filename
from textstego2 import TextSteganography
from ai_suggestions import analyze_image
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
stego = TextSteganography()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_filename(filename):
    """Generate a unique filename using UUID"""
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/embed', methods=['POST'])
def embed():
    if 'image' not in request.files:
        flash('No image uploaded')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PNG or JPG file.')
        return redirect(url_for('index'))
    
    text = request.form.get('text', '')
    if not text:
        flash('No text provided')
        return redirect(url_for('index'))
    
    try:
        # Generate unique filenames
        input_filename = get_unique_filename(file.filename)
        output_filename = f"output_{input_filename}"
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Save uploaded file
        file.save(input_path)
        
        # Process the image
        stego.embed_data(input_path, text, output_path)
        
        # Clean up input file
        os.remove(input_path)
        
        # Send file and schedule cleanup
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as e:
                app.logger.error(f"Error cleaning up file: {e}")
            return response
        
        return send_file(output_path, as_attachment=True, download_name=f"stego_{file.filename}")
    
    except Exception as e:
        for path in [input_path, output_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/extract', methods=['POST'])
def extract():
    if 'image' not in request.files:
        flash('No image uploaded')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PNG or JPG file.')
        return redirect(url_for('index'))
    
    try:
        # Generate unique filename for saving
        input_filename = get_unique_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)

        # Save uploaded file
        file.save(input_path)

        # Extract the text
        extracted_text = stego.extract_data(input_path)
        flash('Text extracted successfully!')

        # Save extracted text as a file with a fixed name
        text_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_file.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        return send_file(text_path, as_attachment=True, download_name='extracted_file.txt')  # Fixed name
    
    except Exception as e:
        flash(f'Error: {str(e)}')
    
    finally:
        # Clean up file
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass
    
    return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_text(filename):
    text_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(text_path):
        return send_file(text_path, as_attachment=True)
    flash('File not found')
    return redirect(url_for('index'))

# New AI Suggestion Route
@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Use PNG, JPG, or JPEG"}), 400
    
    try:
        
        suggestions = analyze_image(file)
        return jsonify(suggestions)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
